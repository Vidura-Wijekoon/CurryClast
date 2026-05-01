interface Props {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
}

export default function PageHeader({ eyebrow, title, subtitle, right }: Props) {
  return (
    <div className="page-header" style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: 24, flexWrap: "wrap" }}>
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {subtitle && <p className="muted" style={{ marginBottom: 0 }}>{subtitle}</p>}
      </div>
      {right}
    </div>
  );
}
