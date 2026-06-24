# Framework

## Introduction 
Dự án xử lý một số vấn đề liên quan đến **Equivalent Mutant Problem (EMP)** trong kiểm thử phần mềm đột biến (Mutation Testing). 
Hiện tại dự án vẫn đang được phát triển bởi nhóm nghiên cứu của chúng tôi, nhằm cung cấp một giải pháp hiệu quả cho bài toán kiểm tra tính tương đương của mã nguồn dựa trên suy luận tự động và mô hình ngôn ngữ lớn (LLMs).

## Architecture 

Dự án được thiết kế với một quy trình bao gồm nhiều giai đoạn (phases) kết hợp giữa phân tích ngữ nghĩa (Semantic Lifting), phân tích cấu trúc (Structural Analysis), và kiểm chứng hình thức (Formal Grounding) thông qua Z3 SMT Solver.

```mermaid
flowchart TD
    Start(["Original Code P_orig & Mutant P_mut"])
    
    subgraph Phase1 ["Phase 1: Semantic Lifting"]
        direction TB
        Prompt["Ensemble Prompting & CoT"]
        Consensus{"Consensus Algorithm"}
        Prompt --> Consensus
    end
    
    Start --> Prompt
    
    Consensus -- "Invariants & Contracts" --> Phase2
    
    subgraph Structural ["Structural Analysis Layers"]
        direction TB
        Phase2["Phase 2: Loops (BMC/Induction)"]
        Phase3["Phase 3: Nested Loops"]
        Phase4["Phase 4: Control Flow (ITE)"]
        Phase5["Phase 5: Functions"]
        Phase7["Phase 7: Concurrency"]
        
        Phase2 --> Phase3
        Phase3 --> Phase4
        Phase4 --> Phase5
        Phase5 --> Phase7
    end
    
    subgraph Formal ["Formal Grounding"]
        direction TB
        Phase6["Phase 6: Formal Bridge (VC Generation)"]
    end
    
    Phase7 --> Phase6
    
    Z3[("Z3 SMT Solver")]
    
    Phase6 --> Z3
    
    UNSAT["UNSAT: Equivalent"]
    SAT["SAT: Counter-example"]
    Indet["Indeterminate"]
    
    Z3 --> UNSAT
    Z3 --> SAT
    Z3 --> Indet
    
    subgraph Phase8 ["Phase 8: Refinement"]
        direction TB
        CEGAR["Self-Correction Loop (CEGAR)"]
    end
    
    Z3 -- "Syntax Error / Unknown" --> CEGAR
    CEGAR -- "Refined Invariants" --> Prompt
    
    classDef startFill fill:#f9e6f2,stroke:#cc99bb,stroke-width:2px,color:#333;
    class Start startFill;
    classDef orange fill:#fff3e6,stroke:#dd9966,stroke-width:2px,color:#333;
    class Phase2,Phase3,Phase4,Phase5,Phase7,Phase6 orange;
    classDef blue fill:#e6f2ff,stroke:#99bbdd,stroke-width:2px,color:#333;
    class Prompt,CEGAR blue;
    classDef diamond fill:#e6f2ff,stroke:#99bbdd,stroke-width:2px,color:#333;
    class Consensus diamond;
    classDef purple fill:#f2e6ff,stroke:#bb99dd,stroke-width:2px,color:#333;
    class UNSAT,SAT,Indet purple;
    classDef db fill:#f9f9f9,stroke:#999999,stroke-width:2px,color:#333;
    class Z3 db;
```

## Features 

Mã nguồn offline trong repository này triển khai một tập hợp con (subset) nhỏ, có thể kiểm thử được của toàn bộ framework:

1. **Structural analysis** cho các loops, branches, function calls, dynamic constructs, và bounded-concurrency flags.
2. **Offline semantic lifting** cho các ví dụ Python nhỏ, do đó repository có thể được kiểm thử mà không cần truy cập LLM được host trực tuyến.
3. **Formal bridge / VC execution** thông qua `z3-solver==4.12.2.0`.
4. **Conservative verdicts** khớp với paper: `Equivalent`, `Non-equivalent`, `Equivalent under Bound`, và `Indeterminate`.
5. **Phase 8 refinement prompts** cho các validation errors, kết quả UNKNOWN, và các candidate counterexamples.

*Lưu ý: Quá trình đánh giá full paper sử dụng một mutant-level manifest lớn hơn và front-end Java/Defects4J. Các cấu trúc không được hỗ trợ trong public prototype này sẽ trả về `Indeterminate` thay vì âm thầm được xấp xỉ là equivalent.*

## Installation 
```bash
pip install -r requirements.txt
```

## Usage 

```bash
python3 src/main.py --original benchmarks/sample_p.py --mutant benchmarks/sample_m.py
```

Expected result for the sample pair:

```text
VERDICT: Equivalent
Reason: UNSAT negated equivalence condition
```

## Tests 

Run all unit tests:

```bash
python3 -m unittest discover tests
```

Run smoke benchmarks:

```bash
python3 scripts/run_benchmarks.py
```
