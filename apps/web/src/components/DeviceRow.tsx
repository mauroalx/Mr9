import Link from "next/link";
import { StatusBadge } from "./StatusBadge";

export type DeviceRowData = {
  id: string;
  serial?: string;
  product_class?: string;
  manufacturer?: string;
  online: boolean;
  last_inform?: string;
  software_version?: string;
};

export function DeviceRow({ device }: { device: DeviceRowData }) {
  return (
    <tr>
      <td>
        <StatusBadge online={device.online} />
      </td>
      <td>
        <Link href={`/devices/${encodeURIComponent(device.id)}`} className="mono" style={{ color: "var(--brand)" }}>
          {device.serial || device.id}
        </Link>
      </td>
      <td>
        {device.manufacturer} · {device.product_class}
      </td>
      <td className="mono">{device.software_version || "—"}</td>
      <td className="mono" style={{ fontSize: 12 }}>
        {device.last_inform || "—"}
      </td>
    </tr>
  );
}
