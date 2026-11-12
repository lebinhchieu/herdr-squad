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
  /** The item's Details page is open (reading page for the whole body). */
  detail: boolean;
  picked: Record<string, string>;
  draft: Record<string, string>;
  pending: string | null;
  notice: InboxNotice | null;
  /** Bumped when a refused send must bring the typed text back into a field the engine cleared. */
  rev: number;
  /** Group keys opened past the 7-row cap (`+N more`). */
  more: string[];
};

// The /squads mod's contract: the `squad-tree --json` document (version 1,
// design-notes section 2) and the pane's own UI state.
export type SquadFacts = {
  needs_you: number | null;
  stuck: number;
  tasks_done: number;
  tasks_total: number;
  agents_working: number | null;
  last_active: string | null;
};

export type NextStep = { rule: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9; text: string };

export type SquadCommand = {
  id: string;
  label: string;
  text: string;
  changes: 'read' | 'writes' | 'destructive' | 'starts';
  runs_by: 'chieu' | 'manager' | 'team';
  group: 'yours' | 'team';
  state: 'ready' | 'wait';
  reason: string | null;
  /** The text holds <text> or <N> that Chieu must replace. */
  placeholder: boolean;
  when: string;
};

export type ScopeNode = {
  name: string;
  kind: 'scope';
  status: 'open' | 'done';
  home: string;
  goal: string | null;
  goal_label: string | null;
  brief: string;
  closed_at: string | null;
  facts: SquadFacts | null;
  unknown: string[];
  next_step: NextStep;
  commands: SquadCommand[];
};

export type GoalNode = {
  name: string;
  kind: 'goal';
  status: 'open' | 'done';
  home: string;
  brief: string;
  closed_at: string | null;
  facts: SquadFacts | null;
  unknown: string[];
  next_step: NextStep;
  commands: SquadCommand[];
  scopes: ScopeNode[];
};

export type SquadNode = {
  name: string;
  flat: boolean;
  message: string | null;
  needs_you: number;
  commands: SquadCommand[];
  goals: GoalNode[];
  scopes: ScopeNode[];
  done: { goals: GoalNode[]; scopes: ScopeNode[] };
};

export type SquadsTree = {
  version: 1;
  repo: string;
  generated: string;
  squads: SquadNode[];
};

export type SquadsUi = {
  isOpen: boolean;
  /** Picked row, e.g. ['plugin', 'goal:g1']; empty = the list screen. */
  path: string[];
  /** Folded group keys. */
  folded: string[];
  /** The `/` name filter. */
  filter: string;
  /** Footer line, e.g. `copied: <command>`. */
  notice: string | null;
};

declare module 'claude-code' {
  interface PluginState {
    squad: {
      /** Last good snapshot; null before the first load and in an inert session. */
      inbox: InboxSnapshot | null;
      /** Why the last refresh failed; null when the last refresh worked. */
      inboxError: string | null;
      ui: InboxUi;
      /** Last good /squads tree; null before the first load. */
      squadsTree: SquadsTree | null;
      /** Why the last squad-tree run failed; null when it worked. */
      squadsError: string | null;
      squadsUi: SquadsUi;
    };
  }
}
