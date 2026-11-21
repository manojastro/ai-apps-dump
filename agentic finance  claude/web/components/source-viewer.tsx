"use client";
import { useEffect, useState } from "react";
import { Spinner } from "@/components/ui";
import { api } from "@/lib/api";

// PDF: server-rendered page image with the figure's bounding box (PDF points) overlaid.
export function PdfSource({ dv, page, bbox, rowBbox }: { dv: string; page: number; bbox: number[] | null; rowBbox: number[] | null }) {
  const [src, setSrc] = useState<string>();
  const [size, setSize] = useState<{ w: number; h: number }>();
  useEffect(() => {
    let url: string | undefined;
    fetch(`/api/engine/documents/${dv}/pages/${page}?dpi=110`).then(async (r) => {
      setSize({ w: Number(r.headers.get("x-page-width-pt")), h: Number(r.headers.get("x-page-height-pt")) });
      url = URL.createObjectURL(await r.blob());
      setSrc(url);
    });
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [dv, page]);
  if (!src || !size) return <Spinner label="Rendering source page" />;
  const box = (b: number[], cls: string, label: string) => (
    <div aria-label={label} className={`absolute ${cls}`} style={{
      left: `${(b[0] / size.w) * 100}%`, top: `${(b[1] / size.h) * 100}%`,
      width: `${((b[2] - b[0]) / size.w) * 100}%`, height: `${((b[3] - b[1]) / size.h) * 100}%`,
    }} />
  );
  return (
    <figure>
      <div className="relative w-full overflow-hidden rounded border border-line bg-white">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src} alt={`Source page ${page}`} className="block w-full" />
        {rowBbox && box([rowBbox[0] - 2, rowBbox[1] - 2, rowBbox[2] + 2, rowBbox[3] + 2], "bg-yellow-300/25", "Source row")}
        {bbox && box([bbox[0] - 3, bbox[1] - 3, bbox[2] + 3, bbox[3] + 3], "border-2 border-red-600 bg-red-500/10", "Exact source cell")}
      </div>
      <figcaption className="mt-1 text-xs text-muted">Page {page}{bbox ? ` · box [${bbox.map((x) => Math.round(x)).join(", ")}] pt` : ""}</figcaption>
    </figure>
  );
}

type Sheet = { sheet: string; focus: string | null; rows: { ref: string; value: string | null }[][]; sheets: string[] };

// XLSX: the worksheet cells around the referenced cell, with the source cell highlighted.
export function SheetSource({ dv, sheet, cell }: { dv: string; sheet: string; cell: string | null }) {
  const [data, setData] = useState<Sheet>();
  useEffect(() => {
    api<Sheet>(`/documents/${dv}/sheet?name=${encodeURIComponent(sheet)}${cell ? `&cell=${cell}` : ""}`).then(setData);
  }, [dv, sheet, cell]);
  if (!data) return <Spinner label="Loading worksheet" />;
  const row = cell ? cell.replace(/^[A-Z]+/, "") : "";
  return (
    <div>
      <div className="mb-1 text-xs text-muted">Worksheet <strong>{data.sheet}</strong>, cell <strong>{cell}</strong> (values only; formulas are never executed)</div>
      <div className="overflow-x-auto rounded border border-line">
        <table className="text-xs">
          <tbody>
            {data.rows.map((r, i) => (
              <tr key={i} className={r[0]?.ref.replace(/^[A-Z]+/, "") === row ? "bg-yellow-100/40" : ""}>
                {r.map((c) => (
                  <td key={c.ref} title={c.ref} className={`border border-line px-1.5 py-0.5 whitespace-nowrap ${c.ref === cell ? "outline outline-2 outline-red-600 font-semibold" : ""}`}>
                    <span className="mr-1 text-[10px] text-muted">{c.ref}</span>{c.value ?? ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
