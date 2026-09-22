---
name: team-meeting-summary
description: >
  Fetches the latest Sophie Society internal team meeting transcript from Roam (primary)
  or Read AI (fallback), generates a structured summary (Key Points → Decisions → Tasks by Person),
  creates tasks in ClickUp under the correct client folder and list (PPC or Content), and posts
  the full summary to #pod-66-team.
  Team members: Nacho, Jeremias Steinmann, Facundo Karchenboim.
  Trigger whenever Nacho says "pasame el resumen de la última reunión de equipo",
  "resumen de la reunión de equipo", "meeting summary del equipo", "summarize last meeting",
  "distribución de tareas de la reunión", or any combination of
  "resumen/summary" + "reunión/meeting" + "equipo/team".
---

# Team Meeting Summary Skill

You are running Sophie Society's team meeting summary workflow. Your job is to fetch the most recent internal team meeting, extract a structured summary, infer task assignments by person, create tasks in ClickUp, and post the summary to the team Slack channel.

---

## Global config

```
Team members:         Nacho | Jeremias Steinmann | Facundo Karchenboim
Slack output channel: #pod-66-team
ClickUp structure:    One folder per client brand → "PPC" list + "Content" list per folder
                      Internal tasks → "Interno" folder
Task naming:          "[Brand Name] - [Task description]"  |  "Interno - [Task description]"
```

---

## Step 1: Fetch the meeting transcript

### 1a. Try Roam Meetings (primary)

Use `Roam Meetings:meeting_list` to retrieve recent meetings.
Filter for meetings that include any of the following participants:
- Jeremias Steinmann
- Facundo Karchenboim

Sort by date descending. Take the most recent match.

```
Roam Meetings:meeting_list → filter by participant name → take latest result
Roam Meetings:meeting_transcript(meeting_id=...) → get full verbatim transcript
```

If a meeting is found and transcript is retrieved → proceed to Step 2.

### 1b. Try Read AI (fallback)

If Roam returns no results or transcript is unavailable, search Read AI for recent meetings:

```
Read AI: search for meetings with Jeremias or Facundo → take most recent
Read AI: fetch full transcript for that meeting
```

If neither source returns a transcript:
- Tell Nacho: "No encontré ninguna reunión de equipo reciente en Roam ni en Read AI. ¿Podés compartir el transcript manualmente?"
- Stop.

---

## Step 2: Generate the structured summary

Parse the full transcript and produce the following three sections. Be assertive and concise — this is an internal document, not a client-facing output.

---

### Output format

```
📋 *Team Meeting Summary — [Date]*
_Participants: Nacho, [others present]_

---

*🔑 Puntos Clave*
• [Key point 1]
• [Key point 2]
• [Key point 3]
... (as many as needed)

---

*✅ Decisiones Tomadas*
• [Decision 1]
• [Decision 2]
... (only include explicit decisions, not open discussions)

---

*🗂 Tareas por Persona*

*Nacho*
• [Brand] - [Task]  _(due: [date] if mentioned)_
• [Brand] - [Task]

*Jeremias*
• [Brand] - [Task]
• Interno - [Task]

*Facundo*
• [Brand] - [Task]
• [Brand] - [Task]

---
_Posted by Sophie Society AI · [Date]_
```

---

### Rules for task extraction

**Assignment inference logic:**
- If the transcript explicitly names a person for a task → assign to them.
- If someone says "I'll do X" or "me encargo de X" → assign to that speaker.
- If a task is directed at someone ("Facundo, revisá X") → assign to that person.
- If the task is ambiguous (no clear owner) → flag it as `❓ Sin asignar - [Brand] - [Task]` and ask Nacho before creating in ClickUp (see Step 3).

**Brand assignment logic:**
- If the task mentions a client brand name → use that brand as prefix.
- If the task is internal (ops, team, tooling, process) with no brand → use "Interno" as prefix.
- If it's unclear which brand → flag for Nacho confirmation before creating in ClickUp (see Step 3).

**PPC vs Content classification:**
- PPC tasks: campaigns, bids, keywords, targeting, search terms, ACOS, TACOS, budget, placements, negatives, harvesting, match types, ad types (SP/SB/SD), scaling.
- Content tasks: listing copy (title, bullets, description), images, A+, brand store, video, infographics, packaging, competitor content review.
- If task doesn't fit either → classify as PPC by default and note it.

---

## Step 3: Clarify ambiguous tasks before ClickUp creation

Before creating any tasks in ClickUp, collect all flagged items (no brand, no owner) and ask Nacho in a single message:

```
Antes de crear las tareas en ClickUp, necesito confirmar algunas cosas:

❓ [Task description sin brand]: ¿A qué cliente corresponde esta tarea?
❓ [Task description sin owner]: ¿A quién se la asignamos — Nacho, Jeremias o Facundo?

Respondé en el formato: "[task] → [Brand] / [Persona]" y continúo con ClickUp.
```

Wait for Nacho's reply before proceeding.
If Nacho says "skip" or "ignorá esa" → omit that task from ClickUp creation.

---

## Step 4: Create tasks in ClickUp

> ⚠️ **ClickUp connector dependency:** This step requires the ClickUp MCP connector to be active.
> If ClickUp is not connected, skip this step silently and note at the end of the Slack message:
> `_⚠️ ClickUp no conectado — tareas no creadas. Conectá el conector para habilitar esta función._`

For each confirmed task (after Step 3 resolution):

### Task creation parameters

| Field | Value |
|---|---|
| **Name** | `[Brand Name] - [Task description]` |
| **List** | `[Client Folder] > PPC` or `[Client Folder] > Content` depending on classification |
| **Assignee** | Nacho / Jeremias Steinmann / Facundo Karchenboim |
| **Due date** | If mentioned in transcript — otherwise leave empty |
| **Description** | If context is available from transcript — brief 1–2 line summary |

### Folder routing

```
Brand task → Find folder matching brand name → route to PPC or Content list
Interno task → "Interno" folder → default to PPC list unless clearly content-related
```

If the brand folder doesn't exist in ClickUp:
- Tell Nacho: "No encontré la carpeta de [Brand] en ClickUp. ¿Querés que la cree o lo hacés vos?"
- Wait for confirmation before creating a new folder.

Create all tasks in a single batch where possible to minimize API calls.

---

## Step 5: Post to Slack

Post the full summary (Step 2 output) directly to `#pod-66-team` using `slack_send_message`.

- Use the Slack search to resolve channel ID for `#pod-66-team` if not cached.
- Always send directly — never draft.
- Append at the bottom of the Slack message a ClickUp status line:

If ClickUp tasks were created:
```
_🗂 Tareas creadas en ClickUp: [N] tareas — [Brand1] (PPC/Content), [Brand2] (PPC), ..._
```

If ClickUp was skipped (not connected):
```
_⚠️ ClickUp no conectado — tareas no creadas._
```

---

## Step 6: Confirm to Nacho in chat

After posting:
```
Listo — resumen enviado a #pod-66-team y [N] tareas creadas en ClickUp.
```

If ClickUp was skipped:
```
Listo — resumen enviado a #pod-66-team. ClickUp no está conectado todavía, pero las tareas están en el resumen de arriba listas para crearse cuando lo conectés.
```

---

## Edge cases

| Situation | Behavior |
|---|---|
| No meeting found in Roam or Read AI | Ask Nacho to share transcript manually, stop |
| Task with no brand | Flag for Nacho confirmation before ClickUp creation |
| Task with no owner | Flag for Nacho confirmation before ClickUp creation |
| Brand folder missing in ClickUp | Ask Nacho before creating new folder |
| ClickUp connector not active | Skip Step 4, note in Slack message |
| Meeting only has 2 of the 3 team members | Normal — only list participants present |
| Multiple meetings found same day | Take the most recent one; tell Nacho which meeting was used |
| Task type ambiguous (PPC vs Content) | Classify as PPC by default, note in task description |
