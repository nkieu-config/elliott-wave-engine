import { Fragment, useMemo } from "react";
import { parseBlocks, splitInline } from "@/lib/narration-format";

function renderInline(text: string) {
  return splitInline(text).map((run, i) =>
    run.bold ? (
      <strong key={i} className="font-semibold text-text">
        {run.text}
      </strong>
    ) : (
      <Fragment key={i}>{run.text}</Fragment>
    ),
  );
}

export function Narration({
  text,
  streaming,
  accent,
}: {
  text: string;
  streaming: boolean;
  accent: string;
}) {
  const blocks = useMemo(() => parseBlocks(text), [text]);
  const cursor = streaming ? (
    <span
      className="inline-block w-[3px] h-[1em] ml-0.5 align-text-bottom animate-caret-blink"
      style={{ background: accent }}
      aria-hidden="true"
    />
  ) : null;

  return (
    <div className="text-[15px] leading-[1.7] font-medium text-text-dim space-y-3.5">
      {blocks.map((b, i) => {
        const isLast = i === blocks.length - 1;
        // Key by index+type so a block changing type mid-stream (p→ul) remounts
        // cleanly instead of reconciling mismatched tags and dropping the cursor.
        const key = `${i}-${b.type}`;
        if (b.type === "ul") {
          return (
            <ul key={key} className="space-y-1.5 pl-5">
              {b.items.map((it, j) => (
                <li key={j} className="list-disc marker:text-faint">
                  {renderInline(it)}
                  {isLast && j === b.items.length - 1 && cursor}
                </li>
              ))}
            </ul>
          );
        }
        if (b.type === "ol") {
          return (
            <ol key={key} className="space-y-1.5 pl-5">
              {b.items.map((it, j) => (
                <li key={j} className="list-decimal marker:text-faint">
                  {renderInline(it)}
                  {isLast && j === b.items.length - 1 && cursor}
                </li>
              ))}
            </ol>
          );
        }
        return (
          <p key={key} className="whitespace-pre-line m-0">
            {renderInline(b.text)}
            {isLast && cursor}
          </p>
        );
      })}
    </div>
  );
}
