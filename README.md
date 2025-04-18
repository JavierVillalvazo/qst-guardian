> [!info] About this project
> **Project Name:** QST Guardian
> **Project Owner:** TBD
> **Version:**  
>  **Date:** 2025-04-14  
> **Commitment date:** May 1st, 2025



## Problem Statement

### Current Context

In the _LightGrid 2.2_ production line, the PSU Tester generates `.qst` files with PSU unit test results.  
**Current Issues:**

- **Unstructured Storage:** Files are saved locally without tracking.
- **Manual Processes:** Audits require manual log searches and Manual registry (Deviation).
- **No record of Test** PASS/FAIL

## Project Objectives

Automate PSU Tester log **automatic** processing for reliable PSU Tested units traceability

## Scope

### In-Scope

| Component                  | Description                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| File System Watcher        | User Interface, File monitoring creation on                                                |
| `.qst` Processing (Parser) | Auto-parsing: Unit Test(Result) & Unit Test Details, results and measurements for all test |
| Database                   | 2 relational tables: `TestHeaders` (Unit Test records), `TestDetails` (failure details)    |

### Out-of-Scope

- Integration with MES & ERP systems.
- User/role management (single user only).
- Functional Test software modifications.
- Defects Tracking - DEBUG, Repairs, Scrap.

## Key Requirements

### Functional Requirements

| **Description**                                                                                                      | **Priority** | **Acceptance Criteria**                                                                                                                                                                                   | Tag                 |
| :------------------------------------------------------------------------------------------------------------------- | :----------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------ |
| Auto-monitor folder `C:/Reports/local_qst/YYYY/mmmm/dd`                                                              | High         | Detects new files within <10 seconds                                                                                                                                                                      | File System Watcher |
| Extract: SerialNumber, TestDate, Node, Result (PASS/FAIL), PSU tester user, ProgramName, ProgramVersion              | High         | 100% of critical fields parsed                                                                                                                                                                            | Parser, SQL Server  |
| Validate duplicates/Retest (Serial + TestDate + Node)                                                                | Medium       | TBD                                                                                                                                                                                                       | TBD                 |
| Extract & Register unit defects: TestName, Limits(lower & upper), Measured Value, Unit(V/W/A) test result(PASS/FAIL) | High         | 10 predifined test types on CFT (Measure 6v test, Measure 15v test, Measure 15vp test ,Voltage load on, Current load on, Active Power load on, Voltage load off, Current load off, Active Power load off) | Parser, SQL Server  |

## Technical Design

```mermaid title:"Process Flow"
flowchart LR
    A[PSU Tester] -->|Generates .qst| B[(Local Folder CFT)]
    B --> C[File System watcher]
    C --> |Python| D{{Parser}}
    D -->|Structured Data| E[(SQL Server)]
    E --> G[GUI]
    C -->|Detects new files | D
```

## Data Model

### Database Diagram

![[CurrentTraceability-db (1).svg]]

## Tech Stack

- **Backend:** Python + Watchdog (monitoring) + PyODBC (SQL Server)
- **Database:** SQL Server (Tables: `TestHeader - Units`, `TestDetails - Defects`)
- **Frontend:** CustomTkinter (local app)

```mermaid
flowchart TB
    %% ========== STYLING ==========
    classDef frontend fill:#e1f5fe,stroke:#039be5,color:#01579b;
    classDef backend fill:#e8f5e9,stroke:#43a047,color:#2e7d32;
    classDef database fill:#fce4ec,stroke:#e91e63,color:#ad1457;
    classDef interaction stroke:#ff9800,stroke-width:2px,stroke-dasharray:5;

    %% ========== FRONTEND COMPONENTS ==========
    subgraph Frontend["Frontend Python"]
        A[("📺 GUI Dashboard")] --> B["📊 Real-Time Log Viewer"]
        A --> C["🛠️ Control Buttons\n(Start/Stop/Pause)"]
        A --> G["⚙️ Settings Panel"]
    end

    %% ========== BACKEND COMPONENTS ==========
    subgraph Backend["Backend Python"]
        D[("🔍 FileSystemWatcher")] -->|"New .QST Files"| E["📝 Parser Engine"]
        E -->|"Parsed Data"| F["📦 SQL Server Database"]
        E -->|"Validation Errors"| J["❌ Error Handler"]
    end

    %% ========== INTERACTIONS ==========
    C <-->|"Commands"| D
    B -.->|"Live Data Stream"| D:::interaction

    %% ========== STYLE ASSIGNMENTS ==========
    class A,B,C,G frontend;
    class D,E,J,H backend;
    class F database;

```

## Next Steps

- To be define
