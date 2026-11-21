import { NavLink, Navigate, Route, Routes, useLocation } from "react-router-dom";
import clsx from "clsx";
import { useAuth } from "./auth";
import { Loading } from "./ui";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import NewRequest from "./pages/NewRequest";
import RunDetail from "./pages/RunDetail";
import Comparison from "./pages/Comparison";
import { ApprovalDetail, ApprovalInbox } from "./pages/Approvals";
import { OrderDetail, Orders } from "./pages/Orders";
import Audit from "./pages/Audit";
import Admin from "./pages/Admin";
import Evals from "./pages/Evals";

function Shell({ children }: { children: React.ReactNode }) {
  const { session, has, logout } = useAuth();
  const links: [string, string, boolean][] = [
    ["/", "Dashboard", true],
    ["/requests/new", "New request", has("requester") || has("admin")],
    ["/approvals", "Approval inbox", true],
    ["/orders", "Orders", true],
    ["/audit", "Audit timeline", true],
    ["/evals", "Evaluation", true],
    ["/admin", "Suppliers & policy", has("admin")],
  ];
  return (
    <div className="flex min-h-full flex-col md:flex-row">
      <aside className="border-b border-line bg-white md:w-60 md:shrink-0 md:border-r md:border-b-0">
        <div className="px-4 py-4">
          <p className="text-base font-semibold">Procurement Navigator</p>
          <p className="text-xs text-muted">{session?.tenant.name}</p>
        </div>
        <nav aria-label="Main" className="flex gap-1 overflow-x-auto px-2 pb-2 md:flex-col md:overflow-visible">
          {links.filter(([, , show]) => show).map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}
              className={({ isActive }) => clsx("whitespace-nowrap rounded-md px-3 py-2 text-sm",
                isActive ? "bg-brand-soft font-medium text-brand" : "text-ink hover:bg-canvas")}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-line px-4 py-2 text-xs md:block md:py-3">
          <p className="font-medium">{session?.user.display_name}</p>
          <p className="text-muted">{session?.user.email}</p>
          <p className="mt-1 flex flex-wrap gap-1">{session?.roles.map((r) => (
            <span key={r} className="rounded bg-canvas px-1.5 py-0.5 text-[11px] text-muted">{r}</span>))}</p>
          <button className="mt-2 text-brand hover:underline" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">{children}</main>
    </div>
  );
}

export default function App() {
  const { session, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div className="p-8"><Loading what="Checking session" /></div>;
  if (!session) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Navigate to="/login" replace state={{ from: loc.pathname }} />} />
      </Routes>
    );
  }
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/requests/new" element={<NewRequest />} />
        <Route path="/runs/:id" element={<RunDetail />} />
        <Route path="/runs/:id/comparison" element={<Comparison />} />
        <Route path="/approvals" element={<ApprovalInbox />} />
        <Route path="/approvals/:id" element={<ApprovalDetail />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/orders/:id" element={<OrderDetail />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/evals" element={<Evals />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="*" element={<p className="text-sm text-muted">Page not found.</p>} />
      </Routes>
    </Shell>
  );
}
