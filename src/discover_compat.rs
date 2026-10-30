//! Private pre-`initialize` `server/discover` compatibility boundary
//! (`056.011-T`, shipment `052-S`).
//!
//! # Defect
//!
//! rmcp 1.5's server handshake tolerates exactly one request before
//! `initialize`: `ping`. Any other first request makes
//! `rmcp::serve_server` return `ServerInitializeError::ExpectedInitializeRequest`,
//! which terminates `serve` and closes the client's pipe. The exact Copilot
//! client opens with `server/discover` (`id: 0`) before `initialize`, so the
//! server died before a normal handshake could occur (see
//! `docs/decisions/2026-08-29-mcp-serve-discover-preinitialize-evidence.md`).
//!
//! # Remedy
//!
//! [`DiscoverCompat`] wraps an already-converted inner
//! `Transport<RoleServer>` and, **only while armed** (before the first
//! inbound `initialize`), answers a `server/discover` request with a
//! correlated JSON-RPC `-32601` (method not found) error, then keeps
//! reading so the normal, unmodified rmcp `initialize` handshake follows.
//!
//! * Exact allowlist: `server/discover` only. Every other message
//!   (including pre-`initialize` `ping`) is forwarded unchanged to rmcp.
//! * No handler, tool, resource, prompt, or `DocServer` state is reachable
//!   from the adapter; the response is built from constants.
//! * A real `DiscoverResult` is never produced.
//! * Bounded: at most [`MAX_DISCOVER_RESPONSES`] discoveries are answered
//!   and only while the admission deadline ([`DISCOVER_ADMISSION_DEADLINE`])
//!   has not passed. The deadline is evaluated when the next inbound
//!   message arrives; it never closes an idle pipe. After either bound is
//!   exhausted the offending message is forwarded unchanged, so rmcp's
//!   existing `ExpectedInitializeRequest` path stays the only termination
//!   path.
//! * At the disarm edge (an inbound `initialize`) the adapter disarms
//!   permanently and becomes a pure passthrough that never calls `send`
//!   itself.
//!
//! # Concurrency model
//!
//! rmcp's [`Transport`] takes `&mut self` for both `receive` and `send`, and
//! `send` returns a `'static` future that may be driven concurrently with
//! `receive`. All adapter state (`armed`, `answered`) is therefore owned by
//! `receive(&mut self)` alone; `send` is a stateless delegation to the inner
//! transport and never reads or writes that state. No shared mutable state
//! exists, so no synchronization primitive is required.
//!
//! # Sunset tripwire
//!
//! This adapter exists only because the rmcp version selected by
//! `056.029-T` does not natively accept a pre-`initialize` `server/discover`.
//! Re-evaluate and remove it (restoring the direct
//! `rmcp::serve_server(server, rmcp::transport::stdio())` composition) when
//! the selected rmcp pin natively tolerates that request.

use std::borrow::Cow;
use std::future::Future;
use std::time::{Duration, Instant};

use rmcp::model::{ClientRequest, ErrorCode, ErrorData, JsonRpcMessage, ServerJsonRpcMessage};
use rmcp::service::{RoleServer, RxJsonRpcMessage, TxJsonRpcMessage};
use rmcp::transport::Transport;
use tracing::{debug, warn};

/// JSON-RPC method name of the only intercepted pre-`initialize` request.
const DISCOVER_METHOD: &str = "server/discover";

/// Maximum number of pre-`initialize` `server/discover` requests answered.
///
/// Live evidence shows a single probe (`id: 0`) per connection; the re-probe
/// cadence is unproven, so a small constant gives a bounded amount of
/// headroom without letting a looping client hold the server pre-`initialize`.
pub(crate) const MAX_DISCOVER_RESPONSES: usize = 4;

/// Window after adapter construction during which `server/discover` may be
/// intercepted. Checked when the next inbound message arrives only.
pub(crate) const DISCOVER_ADMISSION_DEADLINE: Duration = Duration::from_secs(30);

/// Transport adapter that answers pre-`initialize` `server/discover` with a
/// correlated legacy `-32601` error and otherwise passes through.
#[derive(Debug)]
pub(crate) struct DiscoverCompat<T> {
    inner: T,
    armed: bool,
    answered: usize,
    max_answers: usize,
    admission_deadline: Instant,
}

impl<T> DiscoverCompat<T>
where
    T: Transport<RoleServer> + 'static,
{
    /// Wrap `inner` with the production cap and admission deadline.
    pub(crate) fn new(inner: T) -> Self {
        Self::with_limits(inner, MAX_DISCOVER_RESPONSES, DISCOVER_ADMISSION_DEADLINE)
    }

    /// Wrap `inner` with explicit bounds (the deadline is measured from now).
    pub(crate) fn with_limits(inner: T, max_answers: usize, deadline: Duration) -> Self {
        Self {
            inner,
            armed: true,
            answered: 0,
            max_answers,
            admission_deadline: Instant::now() + deadline,
        }
    }

    /// Whether another `server/discover` may still be intercepted.
    fn admits_discover(&self) -> bool {
        self.answered < self.max_answers && Instant::now() <= self.admission_deadline
    }
}

/// Classification of an inbound message while the adapter is armed.
enum Inbound {
    Initialize,
    Discover,
    Other,
}

fn classify(message: &RxJsonRpcMessage<RoleServer>) -> Inbound {
    match message {
        JsonRpcMessage::Request(req) => match &req.request {
            ClientRequest::InitializeRequest(_) => Inbound::Initialize,
            ClientRequest::CustomRequest(custom) if custom.method == DISCOVER_METHOD => {
                Inbound::Discover
            }
            _ => Inbound::Other,
        },
        _ => Inbound::Other,
    }
}

impl<T> Transport<RoleServer> for DiscoverCompat<T>
where
    T: Transport<RoleServer> + 'static,
{
    type Error = T::Error;

    fn name() -> Cow<'static, str> {
        // Keep the underlying transport's diagnostic name so existing
        // user-facing text and assertions are unaffected by the adapter.
        T::name()
    }

    fn send(
        &mut self,
        item: TxJsonRpcMessage<RoleServer>,
    ) -> impl Future<Output = Result<(), Self::Error>> + Send + 'static {
        self.inner.send(item)
    }

    async fn receive(&mut self) -> Option<RxJsonRpcMessage<RoleServer>> {
        loop {
            let message = self.inner.receive().await?;
            if !self.armed {
                return Some(message);
            }
            match classify(&message) {
                Inbound::Initialize => {
                    self.armed = false;
                    return Some(message);
                }
                Inbound::Discover if self.admits_discover() => {
                    let JsonRpcMessage::Request(req) = message else {
                        return Some(message);
                    };
                    self.answered += 1;
                    debug!(
                        answered = self.answered,
                        "answering pre-initialize server/discover with -32601"
                    );
                    let response = ServerJsonRpcMessage::error(
                        ErrorData::new(ErrorCode::METHOD_NOT_FOUND, "Method not found", None),
                        req.id,
                    );
                    if let Err(error) = self.inner.send(response).await {
                        warn!(%error, "failed to send server/discover compatibility response");
                        return None;
                    }
                }
                Inbound::Discover => {
                    // Cap or admission deadline exhausted: stop intercepting
                    // and let rmcp's own ExpectedInitializeRequest path run.
                    self.armed = false;
                    return Some(message);
                }
                Inbound::Other => return Some(message),
            }
        }
    }

    fn close(&mut self) -> impl Future<Output = Result<(), Self::Error>> + Send {
        self.inner.close()
    }
}

#[cfg(test)]
mod tests {
    use std::io;
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::sync::Arc;

    use rmcp::model::{ServerCapabilities, ServerInfo};
    use rmcp::service::ServerInitializeError;
    use rmcp::ServerHandler;
    use serde_json::{json, Value};
    use tokio::sync::mpsc;
    use tokio::time::{sleep, timeout};

    use super::*;

    /// In-memory inner transport: inbound messages come from a channel and
    /// every outbound message is recorded (as JSON) and counted.
    struct MockInner {
        inbound: mpsc::UnboundedReceiver<Value>,
        outbound: mpsc::UnboundedSender<Value>,
        sends: Arc<AtomicUsize>,
    }

    impl Transport<RoleServer> for MockInner {
        type Error = io::Error;

        fn send(
            &mut self,
            item: TxJsonRpcMessage<RoleServer>,
        ) -> impl Future<Output = Result<(), Self::Error>> + Send + 'static {
            let outbound = self.outbound.clone();
            let sends = Arc::clone(&self.sends);
            async move {
                sends.fetch_add(1, Ordering::SeqCst);
                let value = serde_json::to_value(&item).map_err(io::Error::other)?;
                outbound
                    .send(value)
                    .map_err(|_| io::Error::other("outbound closed"))
            }
        }

        async fn receive(&mut self) -> Option<RxJsonRpcMessage<RoleServer>> {
            let value = self.inbound.recv().await?;
            Some(serde_json::from_value(value).expect("valid client message"))
        }

        fn close(&mut self) -> impl Future<Output = Result<(), Self::Error>> + Send {
            std::future::ready(Ok(()))
        }
    }

    struct Harness {
        to_server: mpsc::UnboundedSender<Value>,
        from_server: mpsc::UnboundedReceiver<Value>,
        sends: Arc<AtomicUsize>,
        inner: MockInner,
    }

    fn harness() -> Harness {
        let (to_server, inbound) = mpsc::unbounded_channel();
        let (outbound, from_server) = mpsc::unbounded_channel();
        let sends = Arc::new(AtomicUsize::new(0));
        Harness {
            to_server,
            from_server,
            sends: Arc::clone(&sends),
            inner: MockInner {
                inbound,
                outbound,
                sends,
            },
        }
    }

    #[derive(Debug)]
    struct TestHandler;

    impl ServerHandler for TestHandler {
        fn get_info(&self) -> ServerInfo {
            ServerInfo::new(ServerCapabilities::builder().enable_tools().build())
        }
    }

    fn discover(id: u64) -> Value {
        json!({"jsonrpc":"2.0","id":id,"method":"server/discover","params":{}})
    }

    fn initialize(id: u64) -> Value {
        json!({
            "jsonrpc":"2.0","id":id,"method":"initialize",
            "params":{
                "protocolVersion":"2025-06-18",
                "capabilities":{},
                "clientInfo":{"name":"test","version":"0"}
            }
        })
    }

    fn request(id: u64, method: &str) -> Value {
        json!({"jsonrpc":"2.0","id":id,"method":method})
    }

    async fn next_out(h: &mut Harness) -> Value {
        timeout(Duration::from_secs(5), h.from_server.recv())
            .await
            .expect("timed out waiting for server message")
            .expect("server closed")
    }

    // ── RED-1 / green: continued handshake after server/discover ─────────

    #[tokio::test]
    async fn discover_then_initialize_continues_to_tools() {
        let mut h = harness();
        h.to_server.send(discover(0)).unwrap();
        h.to_server.send(initialize(1)).unwrap();
        let adapter = DiscoverCompat::new(h.inner_take());
        let running = rmcp::serve_server(TestHandler, adapter)
            .await
            .expect("handshake must continue after server/discover");

        let discover_reply = next_out(&mut h).await;
        assert_eq!(discover_reply["jsonrpc"], "2.0");
        assert_eq!(discover_reply["id"], 0);
        assert_eq!(discover_reply["error"]["code"], -32601);
        assert!(discover_reply.get("result").is_none());

        let init_reply = next_out(&mut h).await;
        assert_eq!(init_reply["id"], 1);
        assert!(init_reply["result"]["protocolVersion"].is_string());
        assert!(init_reply.get("error").is_none());

        h.to_server
            .send(json!({"jsonrpc":"2.0","method":"notifications/initialized"}))
            .unwrap();
        h.to_server.send(request(2, "tools/list")).unwrap();
        let tools_reply = next_out(&mut h).await;
        assert_eq!(tools_reply["id"], 2);
        assert!(tools_reply["result"]["tools"].is_array());
        // Exactly: one discover reply, one initialize reply, one tools reply.
        assert_eq!(h.sends.load(Ordering::SeqCst), 3);
        drop(running);
    }

    // ── C-1: non-allowlisted pre-initialize request fails closed ─────────

    #[tokio::test]
    async fn non_allowlisted_pre_initialize_request_fails_closed_with_zero_sends() {
        let mut h = harness();
        h.to_server.send(request(0, "tools/list")).unwrap();
        let adapter = DiscoverCompat::new(h.inner_take());
        let err = rmcp::serve_server(TestHandler, adapter)
            .await
            .expect_err("must fail closed");
        assert!(matches!(
            err,
            ServerInitializeError::ExpectedInitializeRequest(_)
        ));
        assert_eq!(h.sends.load(Ordering::SeqCst), 0);
    }

    // ── C-2: ping stays rmcp passthrough and the handshake completes ─────

    #[tokio::test]
    async fn ping_remains_passthrough_then_initializes() {
        let mut h = harness();
        h.to_server.send(request(0, "ping")).unwrap();
        h.to_server.send(initialize(1)).unwrap();
        let adapter = DiscoverCompat::new(h.inner_take());
        let running = rmcp::serve_server(TestHandler, adapter)
            .await
            .expect("ping then initialize must succeed");
        let ping_reply = next_out(&mut h).await;
        assert_eq!(ping_reply["id"], 0);
        assert_eq!(ping_reply["result"], json!({}));
        let init_reply = next_out(&mut h).await;
        assert_eq!(init_reply["id"], 1);
        assert!(init_reply["result"]["protocolVersion"].is_string());
        drop(running);
    }

    // ── C-3: cap / admission deadline forward unchanged ──────────────────

    #[tokio::test]
    async fn cap_exhaustion_forwards_discover_to_rmcp() {
        let mut h = harness();
        h.to_server.send(discover(0)).unwrap();
        h.to_server.send(discover(1)).unwrap();
        h.to_server.send(initialize(2)).unwrap();
        let adapter = DiscoverCompat::with_limits(h.inner_take(), 1, Duration::from_secs(60));
        let err = rmcp::serve_server(TestHandler, adapter)
            .await
            .expect_err("second discover must reach rmcp unchanged");
        assert!(matches!(
            err,
            ServerInitializeError::ExpectedInitializeRequest(_)
        ));
        assert_eq!(h.sends.load(Ordering::SeqCst), 1);
        assert_eq!(next_out(&mut h).await["id"], 0);
    }

    #[tokio::test]
    async fn discover_after_admission_deadline_forwards_to_rmcp() {
        let mut h = harness();
        let adapter = DiscoverCompat::with_limits(h.inner_take(), 4, Duration::from_millis(1));
        sleep(Duration::from_millis(20)).await;
        h.to_server.send(discover(0)).unwrap();
        let err = rmcp::serve_server(TestHandler, adapter)
            .await
            .expect_err("late discover must reach rmcp unchanged");
        assert!(matches!(
            err,
            ServerInitializeError::ExpectedInitializeRequest(_)
        ));
        assert_eq!(h.sends.load(Ordering::SeqCst), 0);
    }

    // ── RED-5 and direct adapter-level seams ─────────────────────────────

    #[tokio::test]
    async fn one_send_per_intercepted_request_and_none_for_other_messages() {
        let mut h = harness();
        let mut adapter = DiscoverCompat::new(h.inner_take());
        h.to_server.send(discover(7)).unwrap();
        h.to_server.send(request(8, "tools/list")).unwrap();
        let forwarded = adapter.receive().await.expect("forwarded message");
        // discover consumed (one send), tools/list forwarded (zero sends).
        assert_eq!(h.sends.load(Ordering::SeqCst), 1);
        match forwarded {
            JsonRpcMessage::Request(req) => {
                assert!(matches!(req.request, ClientRequest::ListToolsRequest(_)));
            }
            other => panic!("unexpected message: {other:?}"),
        }
        assert_eq!(next_out(&mut h).await["id"], 7);
    }

    // ── C-4 / C-5 / disarm-edge ──────────────────────────────────────────

    #[tokio::test]
    async fn post_initialize_discover_passes_through_untouched_after_idle() {
        let mut h = harness();
        let mut adapter = DiscoverCompat::with_limits(h.inner_take(), 4, Duration::from_millis(1));
        h.to_server.send(initialize(1)).unwrap();
        assert!(adapter.receive().await.is_some());
        // Long-idle (past the admission deadline) post-initialize session
        // is never terminated by the adapter.
        sleep(Duration::from_millis(30)).await;
        h.to_server.send(discover(2)).unwrap();
        let message = adapter.receive().await.expect("pure passthrough");
        match message {
            JsonRpcMessage::Request(req) => {
                assert!(matches!(req.request, ClientRequest::CustomRequest(_)));
            }
            other => panic!("unexpected message: {other:?}"),
        }
        assert_eq!(h.sends.load(Ordering::SeqCst), 0);
    }

    #[tokio::test]
    async fn disarm_edge_is_independent_of_concurrent_outbound_sends() {
        let mut h = harness();
        let mut adapter = DiscoverCompat::new(h.inner_take());
        // An outbound send future is created and driven concurrently with
        // receive(); it must not touch or race adapter state.
        let outbound = adapter.send(ServerJsonRpcMessage::error(
            ErrorData::new(ErrorCode::INTERNAL_ERROR, "x", None),
            rmcp::model::NumberOrString::Number(99),
        ));
        let sender = tokio::spawn(outbound);
        h.to_server.send(discover(0)).unwrap();
        h.to_server.send(initialize(1)).unwrap();
        h.to_server.send(discover(2)).unwrap();
        let first = adapter.receive().await.expect("initialize forwarded");
        assert!(matches!(
            first,
            JsonRpcMessage::Request(ref r) if matches!(r.request, ClientRequest::InitializeRequest(_))
        ));
        sender.await.unwrap().unwrap();
        // After the disarm edge the next discover is forwarded, not answered.
        let second = adapter.receive().await.expect("discover forwarded");
        assert!(matches!(
            second,
            JsonRpcMessage::Request(ref r) if matches!(r.request, ClientRequest::CustomRequest(_))
        ));
        // Sends: 1 discover reply + 1 concurrent outbound; none after disarm.
        assert_eq!(h.sends.load(Ordering::SeqCst), 2);
    }

    impl Harness {
        /// Move the inner transport out (it is consumed by the adapter).
        fn inner_take(&mut self) -> MockInner {
            let (_tx, rx) = mpsc::unbounded_channel();
            let (otx, _orx) = mpsc::unbounded_channel();
            std::mem::replace(
                &mut self.inner,
                MockInner {
                    inbound: rx,
                    outbound: otx,
                    sends: Arc::new(AtomicUsize::new(0)),
                },
            )
        }
    }
}
