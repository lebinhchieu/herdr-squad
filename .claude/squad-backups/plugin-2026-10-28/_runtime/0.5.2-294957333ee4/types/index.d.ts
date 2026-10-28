// The po-inbox mod's contract: the `squad-inbox list --json` snapshot (version 1,
// design.md "The contract") and the session state the band and pane read.
export type InboxOption = { key: string; text: string };

export type InboxAnswer = {
  text: string;
  option: string | null;
  note: string | null;
  ts: string;
  source: 'pane' | 'chat';
  delivered_ts: string | null;
};

export type InboxDone = {
  kind: 'read' | 'answered' | 'answered-file' | 'withdrawn' | 'removed';
  ts: string;
  reason: string | null;
};

export type InboxItem = {
  id: string;
  kind: 'answer' | 'read';
  state: 'open' | 'answered-waiting' | 'done';
  title: string;
  body: string;
  options: InboxOption[] | null;
  recommendation: string | null;
  blocks: string;
  created: string;
  created_precision?: 'day' | 'second';
  /** The Options cell as written, when it did not parse (options is null); absent otherwise. */
  options_raw?: string | null;
  answer: InboxAnswer | null;
  done: InboxDone | null;
  flags: string[];
};

export type InboxSnapshot = {
  version: 1;
  home: string;
  now: string;
  counts: { answer_open: number; read_open: number; waiting: number };
  items: InboxItem[];
  errors: { file: string; row: number; message: string }[];
};

export type InboxNotice = { tone: 'ok' | 'error'; text: string };

export type InboxUi = {
  isOpen: boolean;
  screen: 'list' | 'item' | 'done' | 'doneItem';
  id: string | null;
  expanded: boolean;
  picked: Record<string, string>;
  draft: Record<string, string>;
  pending: string | null;
  notice: InboxNotice | null;
  /** Bumped when a refused send must bring the typed text back into a field the engine cleared. */
  rev: number;
  /** Group keys opened past the 7-row cap (`+N more`). */
  more: string[];
};

declare module 'claude-code' {
  interface PluginState {
    squad: {
      /** Last good snapshot; null before the first load and in an inert session. */
      inbox: InboxSnapshot | null;
      /** Why the last refresh failed; null when the last refresh worked. */
      inboxError: string | null;
      ui: InboxUi;
    };
  }
}
