SYSTEM_PROMPT_TEMPLATE_JAVA = """
You are an expert security researcher specializing in Java static analysis and vulnerability detection.

ROLE & OBJECTIVE:
You are auditing a Java code snippet that has been flagged because it uses a security-sensitive API (sink). Your task is to determine whether this sensitive API usage is adequately protected against {vulnerability_type} and other exploitable vulnerabilities.

ANALYSIS SCOPE (CRITICAL FOR ACCURACY):
- Focus on the target function and its direct data flow to the sensitive API (sink).
- DO NOT flag code smells, missing best practices, or theoretical edge cases that are not exploitable.

OUTPUT REQUIREMENTS:
Your response must be a single, valid JSON object.
- DO NOT use Markdown blocks (e.g., no ```json).
- DO NOT add text, notes, or comments outside the JSON.
- Escape all special characters correctly.

REQUIRED JSON STRUCTURE:
{{
    "explanation": "<Your step-by-step reasoning>",
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""

USER_PROMPT_TEMPLATE_JAVA = """
TASK
- Analyze the following code in a Java project and Determine whether the following Java snippet indicates a {vulnerability_type} vulnerability.

CONTEXT (do not assume anything not shown)
- Target function: {target_function_name}
- Sensitive API: {sensitive_api}

CODE
{code_snippet}

ANALYSIS STRUCTURE (keep it inside the JSON field "explanation")
1) Initialization: start the explanation with the exact phrase: Let's think step by step.
2) Context analysis: infer what frameworks/libraries are in play from imports and how they may sanitize/validate data, and then evaluate the capabilities of the methods within these third-party libraries.
3) Guideline-informed hypothesis generation (NON-BINDING):
   - Use {cwe_guideline} as a lens to enumerate a small set of plausible validation gaps relevant to this code (e.g., type/format/length/range/whitelist/boundaries/context-specific).
   - For each hypothesized gap:
     - State what concrete evidence would confirm it (what to look for in missing code paths).
     - State what evidence in the snippet weakens it (if any).
   - Do NOT require that every guideline item be checked; only discuss items that plausibly apply to this snippet.
4) Dataflow tracing:
    -   Identify possible sources, transformations, sanitizers/validators, and the sink in the code snippet; state whether a continuous tainted path exists.
    -   Decide whether the snippet shows a *confirmed* continuous untrusted flow to the sink, or only a *possible* one.
    -   Distinguish:
     - Confirmed tainted path (evidence in snippet)
     - Potential tainted path (requires missing context)
     - Broken/mitigated path (evidence of validation/sanitization)
5) Self-check:
    -   Before concluding, review your analysis for any missed details.
    -   Ask: "Am I concluding vulnerability purely from absence of evidence?"
    -   Ask: "Could validation occur outside the shown function (filters/interceptors/annotations/helpers)?"
    -   If uncertainty is high, lower confidence rather than forcing a definite verdict.
6) Final output:
    -   Conclude with a strict JSON object. Do not include markdown formatting (like ```json) inside the JSON block definition, but ensure the final block is a valid JSON.
    -   "is_vulnerable" should be true only if there is direct evidence in the snippet of improper/insufficient validation in a security-relevant path.
    -   If evidence is insufficient, set "is_vulnerable" to false but reduce confidence_score (or keep it mid/low) and explain uncertainty.

OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "explanation": <YOUR STEP-BY-STEP REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""

USER_PROMPT_TEMPLATE_WITH_IMPORTS_JAVA = """
TASK
- Analyze the following code in a Java project and Determine whether the following Java snippet indicates a {vulnerability_type} vulnerability.

CONTEXT (do not assume anything not shown)
- Target function: {target_function_name}
- Sensitive API: {sensitive_api}
- Imports (may include 3rd-party): {imports}

CODE
{code_snippet}

ANALYSIS STRUCTURE (keep it inside the JSON field "explanation")
1) Initialization: start the explanation with the exact phrase: Let's think step by step.
2) Context analysis: infer what frameworks/libraries are in play from imports and how they may sanitize/validate data, and then evaluate the capabilities of the methods within these third-party libraries.
3) Guideline-informed hypothesis generation (NON-BINDING):
   - Use {cwe_guideline} as a lens to enumerate a small set of plausible validation gaps relevant to this code (e.g., type/format/length/range/whitelist/boundaries/context-specific).
   - For each hypothesized gap:
     - State what concrete evidence would confirm it (what to look for in missing code paths).
     - State what evidence in the snippet weakens it (if any).
   - Do NOT require that every guideline item be checked; only discuss items that plausibly apply to this snippet.
4) Dataflow tracing:
    -   Identify possible sources, transformations, sanitizers/validators, and the sink in the code snippet; state whether a continuous tainted path exists.
    -   Decide whether the snippet shows a *confirmed* continuous untrusted flow to the sink, or only a *possible* one.
    -   Distinguish:
     - Confirmed tainted path (evidence in snippet)
     - Potential tainted path (requires missing context)
     - Broken/mitigated path (evidence of validation/sanitization)
5) Self-check:
    -   Before concluding, review your analysis for any missed details.
    -   Ask: "Am I concluding vulnerability purely from absence of evidence?"
    -   Ask: "Could validation occur outside the shown function (filters/interceptors/annotations/helpers)?"
    -   If uncertainty is high, lower confidence rather than forcing a definite verdict.
6) Final output:
    -   Conclude with a strict JSON object. Do not include markdown formatting (like ```json) inside the JSON block definition, but ensure the final block is a valid JSON.
    -   "is_vulnerable" should be true only if there is direct evidence in the snippet of improper/insufficient validation in a security-relevant path.
    -   If evidence is insufficient, set "is_vulnerable" to false but reduce confidence_score (or keep it mid/low) and explain uncertainty.

OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "explanation": <YOUR STEP-BY-STEP REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""


USER_PROMPT_TEMPLATE_WITH_IMPORTS_JAVA = """
TASK
- Analyze the following code in a Java project and Determine whether the following Java snippet indicates a {vulnerability_type} vulnerability.

CONTEXT (do not assume anything not shown)
- Target function: {target_function_name}
- Sensitive API (sink candidate): {sensitive_api}
- Imports (may include 3rd-party): {imports}

CODE
{code_snippet}

ANALYSIS STRUCTURE (keep it inside the JSON field "explanation")
1) Initialization: start the explanation with the exact phrase: Let's think step by step.
2) Context analysis: infer what frameworks/libraries are in play from imports and how they may sanitize/validate data, and then evaluate the capabilities of the methods within these third-party libraries.
3) Dataflow tracing: identify possible sources, transformations, sanitizers/validators, and the sink in the code snippet; state whether a continuous tainted path exists.
4) Self-check:
    -   Before concluding, review your analysis for any missed details.
    -   Ask yourself: "Did I miss any implicit sanitization provided by the framework?" or "Is the data flow strictly continuous?"
    -   Ensure the final verdict is logically derived from the evidence found in the code snippet.
5) Final output:
    -   Conclude with a strict JSON object. Do not include markdown formatting (like ```json) inside the JSON block definition, but ensure the final block is a valid JSON.

OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "explanation": <YOUR STEP-BY-STEP REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""

SYSTEM_PROMPT_TEMPLATE_C_CPP = """
You are an expert in detecting security vulnerabilities.
You are given the code snippet in a C/C++ project with relevant context information. 
Your goal: Analyze the given function with its context information and predict whether the given dataflow can be part of a {vulnerability_type} vulnerability.
Please first think step by step to ensure a logical analysis, and then associate it with the verdict.
If you need more context information, specify it in the explanation.

Answer in JSON object with the following format:

EXAMPLE JSON OUTPUT:
{{
    "explanation": <YOUR STEP-BY-STEP REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}

** REMEMBER **
- DO NOT add any Markdown format like ```json ```
- DO NOT add any additional text outside the JSON object.
- DO NOT include any explanations, notes, or comments outside the JSON object.
- Your output must strictly follow the JSON format provided above.
- Your should escape all special characters in the JSON object correctly, e.g., '"' should be escaped as '\\"'
"""

USER_PROMPT_TEMPLATE_C_CPP = """
TASK
- Analyze the following code in a C/C++ project and Determine whether the following C/C++ snippet indicates a {vulnerability_type} vulnerability.

CONTEXT (do not assume anything not shown)
- Target function: {target_function_name}
- Sensitive API: {sensitive_api}

CODE
{code_snippet}

ANALYSIS STRUCTURE (keep it inside the JSON field "explanation")
1) Initialization: start the explanation with the exact phrase: Let's think step by step.
2) Context analysis: infer what frameworks/libraries are in play from imports and how they may sanitize/validate data, and then evaluate the capabilities of the methods within these third-party libraries.
3) Guideline-informed hypothesis generation (NON-BINDING):
   - Use {cwe_guideline} as a lens to enumerate a small set of plausible validation gaps relevant to this code (e.g., type/format/length/range/whitelist/boundaries/context-specific).
   - For each hypothesized gap:
     - State what concrete evidence would confirm it (what to look for in missing code paths).
     - State what evidence in the snippet weakens it (if any).
   - Do NOT require that every guideline item be checked; only discuss items that plausibly apply to this snippet.
4) Dataflow tracing:
    -   Identify possible sources, transformations, sanitizers/validators, and the sink in the code snippet; state whether a continuous tainted path exists.
    -   Decide whether the snippet shows a *confirmed* continuous untrusted flow to the sink, or only a *possible* one.
    -   Distinguish:
     - Confirmed tainted path (evidence in snippet)
     - Potential tainted path (requires missing context)
     - Broken/mitigated path (evidence of validation/sanitization)
5) Self-check:
    -   Before concluding, review your analysis for any missed details.
    -   Ask: "Am I concluding vulnerability purely from absence of evidence?"
    -   Ask: "Could validation occur outside the shown function (filters/interceptors/annotations/helpers)?"
    -   If uncertainty is high, lower confidence rather than forcing a definite verdict.
6) Final output:
    -   Conclude with a strict JSON object. Do not include markdown formatting (like ```json) inside the JSON block definition, but ensure the final block is a valid JSON.
    -   "is_vulnerable" should be true only if there is direct evidence in the snippet of improper/insufficient validation in a security-relevant path.
    -   If evidence is insufficient, set "is_vulnerable" to false but reduce confidence_score (or keep it mid/low) and explain uncertainty.

OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "explanation": <YOUR STEP-BY-STEP REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""

SYSTEM_PROMPT_TEMPLATE_W_O_CoT_JAVA = """
You are an expert in detecting security vulnerabilities.
You are given a Java method code snippet. 
Your goal: Let's think step by step to determine whether the following Java method code snippet is buggy?

Answer in JSON object with the following format:
{{
    "is_vulnerable": <true or false>,
}}
"""
USER_PROMPT_TEMPLATE_W_O_CoT_JAVA = """
Let's think step by step to determine whether the following Java method code snippet is buggy?
CODE
{code_snippet}
OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "is_vulnerable": <true or false>,
}}
"""

# ---------------------------------------------------------------------------
# Reflection prompt templates
# ---------------------------------------------------------------------------

REFLECTION_SYSTEM_PROMPT_TEMPLATE_JAVA = """
You are a senior security auditor performing a second-pass review.
A previous analysis has already been conducted on a Java code snippet to determine whether a {vulnerability_type} vulnerability exists.
Your task is to critically reflect on that initial analysis: verify its reasoning, check for logical gaps, missed sanitization, or false assumptions, and then deliver your own independent final verdict.

Answer in JSON object with the following format:

EXAMPLE JSON OUTPUT:
{{
    "explanation": <YOUR REFLECTION AND FINAL REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}

** REMEMBER **
- DO NOT add any Markdown format like ```json ```
- DO NOT add any additional text outside the JSON object.
- DO NOT include any explanations, notes, or comments outside the JSON object.
- Your output must strictly follow the JSON format provided above.
- Your should escape all special characters in the JSON object correctly, e.g., '"' should be escaped as '\\"'
"""

REFLECTION_USER_PROMPT_TEMPLATE_JAVA = """
TASK
- A previous vulnerability analysis has been performed on the following Java code snippet for {vulnerability_type}. Your job is to reflect on the initial analysis, identify any errors or oversights, and provide your final verdict.

CONTEXT (do not assume anything not shown)
- Target function: {target_function_name}
- Sensitive API (sink candidate): {sensitive_api}

CODE
{code_snippet}

INITIAL ANALYSIS RESULT
- Verdict: is_vulnerable = {initial_is_vulnerable}
- Confidence: {initial_confidence_score}/10
- Reasoning: {initial_explanation}

REFLECTION INSTRUCTIONS
1) Re-read the code snippet carefully and independently trace the dataflow.
2) Evaluate the initial analysis:
    - Is the dataflow tracing correct? Are there sources, transformations, or sanitizers that were missed or misidentified?
    - Does the initial reasoning contain any logical leaps or unsupported assumptions?
    - Was any implicit framework-level protection overlooked or incorrectly assumed?
    - Is the conclusion consistent with the evidence presented?
3) Consider counter-arguments:
    - If the initial verdict was "vulnerable", look for evidence that might refute it (e.g., hidden sanitization, safe API usage, framework guarantees).
    - If the initial verdict was "not vulnerable", look for evidence that might indicate a real vulnerability (e.g., missing validation, unguarded paths).
4) Deliver your final verdict based on your own analysis. You may agree or disagree with the initial result.

OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "explanation": <YOUR REFLECTION AND FINAL REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""

REFLECTION_USER_PROMPT_TEMPLATE_WITH_IMPORTS_JAVA = """
TASK
- A previous vulnerability analysis has been performed on the following Java code snippet for {vulnerability_type}. Your job is to reflect on the initial analysis, identify any errors or oversights, and provide your final verdict.

CONTEXT (do not assume anything not shown)
- Target function: {target_function_name}
- Sensitive API (sink candidate): {sensitive_api}
- Imports (may include 3rd-party): {imports}

CODE
{code_snippet}

INITIAL ANALYSIS RESULT
- Verdict: is_vulnerable = {initial_is_vulnerable}
- Confidence: {initial_confidence_score}/10
- Reasoning: {initial_explanation}

REFLECTION INSTRUCTIONS
1) Re-read the code snippet carefully and independently trace the dataflow.
2) Evaluate the initial analysis:
    - Is the dataflow tracing correct? Are there sources, transformations, or sanitizers that were missed or misidentified?
    - Does the initial reasoning contain any logical leaps or unsupported assumptions?
    - Was any implicit framework-level protection overlooked or incorrectly assumed?
    - Is the conclusion consistent with the evidence presented?
3) Consider counter-arguments:
    - If the initial verdict was "vulnerable", look for evidence that might refute it (e.g., hidden sanitization, safe API usage, framework guarantees).
    - If the initial verdict was "not vulnerable", look for evidence that might indicate a real vulnerability (e.g., missing validation, unguarded paths).
4) Deliver your final verdict based on your own analysis. You may agree or disagree with the initial result.

OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "explanation": <YOUR REFLECTION AND FINAL REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""

REFLECTION_SYSTEM_PROMPT_TEMPLATE_C_CPP = """
You are a senior security auditor performing a second-pass review.
A previous analysis has already been conducted on a C/C++ code snippet to determine whether a {vulnerability_type} vulnerability exists.
Your task is to critically reflect on that initial analysis: verify its reasoning, check for logical gaps, missed sanitization, or false assumptions, and then deliver your own independent final verdict.

Answer in JSON object with the following format:

EXAMPLE JSON OUTPUT:
{{
    "explanation": <YOUR REFLECTION AND FINAL REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}

** REMEMBER **
- DO NOT add any Markdown format like ```json ```
- DO NOT add any additional text outside the JSON object.
- DO NOT include any explanations, notes, or comments outside the JSON object.
- Your output must strictly follow the JSON format provided above.
- Your should escape all special characters in the JSON object correctly, e.g., '"' should be escaped as '\\"'
"""

REFLECTION_USER_PROMPT_TEMPLATE_C_CPP = """
TASK
- A previous vulnerability analysis has been performed on the following C/C++ code snippet for {vulnerability_type}. Your job is to reflect on the initial analysis, identify any errors or oversights, and provide your final verdict.

CONTEXT (do not assume anything not shown)
- Target function: {target_function_name}
- Sensitive API: {sensitive_api}

CODE
{code_snippet}

INITIAL ANALYSIS RESULT
- Verdict: is_vulnerable = {initial_is_vulnerable}
- Confidence: {initial_confidence_score}/10
- Reasoning: {initial_explanation}

REFLECTION INSTRUCTIONS
1) Re-read the code snippet carefully and independently trace the dataflow.
2) Evaluate the initial analysis:
    - Is the dataflow tracing correct? Are there sources, transformations, or sanitizers that were missed or misidentified?
    - Does the initial reasoning contain any logical leaps or unsupported assumptions?
    - Was any implicit framework-level protection overlooked or incorrectly assumed?
    - Is the conclusion consistent with the evidence presented?
3) Consider counter-arguments:
    - If the initial verdict was "vulnerable", look for evidence that might refute it (e.g., hidden sanitization, safe API usage, framework guarantees).
    - If the initial verdict was "not vulnerable", look for evidence that might indicate a real vulnerability (e.g., missing validation, unguarded paths).
4) Deliver your final verdict based on your own analysis. You may agree or disagree with the initial result.

OUTPUT JSON SHAPE (for reference; your response must be the JSON object only)
{{
    "explanation": <YOUR REFLECTION AND FINAL REASONING>,
    "is_vulnerable": <true or false>,
    "confidence_score": <1-10>
}}
"""