interface Props {
  label: string;
  value: string | number;
  footnote?: string;
}

export default function Metric({ label, value, footnote }: Props) {
  return (
    <div className="metric">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {footnote && <div className="footnote">{footnote}</div>}
    </div>
  );
}
