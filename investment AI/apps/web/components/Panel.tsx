export function Panel({
  title,
  children,
  kicker,
}: {
  title?: string;
  kicker?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border border-rule bg-raised p-5">
      {kicker ? <p className="mb-1 text-sm text-brass">{kicker}</p> : null}
      {title ? <h2 className="font-display text-2xl text-navy">{title}</h2> : null}
      <div className={title ? "mt-4" : ""}>{children}</div>
    </section>
  );
}
