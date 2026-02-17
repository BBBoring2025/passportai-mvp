"use client";

const STATUS_COLORS: Record<string, string> = {
  // Case / Document statuses
  draft: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300",
  processing:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  ready_l1:
    "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  ready_l2:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  blocked:
    "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  closed:
    "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
  uploaded:
    "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
  text_extracted:
    "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300",
  classified:
    "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
  extracted:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  error:
    "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  // Field statuses
  pending_review:
    "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  approved:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  conflict:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  rejected:
    "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  missing:
    "bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400",
  // Checklist statuses
  open: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300",
  done: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  reopened:
    "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  // Validation statuses
  pass: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  fail: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300",
  warn: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Taslak",
  processing: "Isleniyor",
  ready_l1: "L1 Hazir",
  ready_l2: "L2 Hazir",
  blocked: "Engellendi",
  closed: "Kapandi",
  uploaded: "Yuklendi",
  text_extracted: "Metin Cikarildi",
  classified: "Siniflandirildi",
  extracted: "Veri Cikarildi",
  error: "Hata",
  // Field statuses
  pending_review: "Inceleme Bekliyor",
  approved: "Onaylandi",
  conflict: "Celiskili",
  rejected: "Reddedildi",
  missing: "Eksik",
  // Checklist statuses
  open: "Acik",
  done: "Tamamlandi",
  reopened: "Yeniden Acildi",
  // Validation statuses
  pass: "Gecti",
  fail: "Basarisiz",
  warn: "Uyari",
};

export default function StatusBadge({ status }: { status: string }) {
  const colors =
    STATUS_COLORS[status] ||
    "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
  const label = STATUS_LABELS[status] || status;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors}`}
    >
      {label}
    </span>
  );
}
