
    const { useState, useEffect } = React;

    const API_BASE = "http://127.0.0.1:8000/api/v1";

    const ALL_AGENTS_CONFIG = [
      { id: "mom", name: "MOM Agent", desc: "Minutes of Meeting & Action Items", icon: "fa-list-check" },
      { id: "user-stories", name: "Agile Stories", desc: "INVEST User Stories & BDD Criteria", icon: "fa-cubes" },
      { id: "ddl3", name: "DDL3 Design", desc: "Functional, Technical & Config DDL3 Specs", icon: "fa-diagram-project" },
      { id: "test", name: "Test Agent", desc: "FIT/UAT Inventory & Manual Test Cases", icon: "fa-vial" },
      { id: "readiness-scoring", name: "Readiness & Audit", desc: "Delivery Readiness Scoring & SDLC Audit", icon: "fa-bullseye" },
      { id: "gap-analysis", name: "Gap Analysis & RTM", desc: "Requirement Gap Analysis & Traceability Matrix", icon: "fa-magnifying-glass" },
      { id: "change-impact", name: "Change Impact", desc: "Change Impact Assessment & Interdependency Matrix", icon: "fa-route" },
      { id: "kdd-package", name: "KDD for DAB", desc: "Knowledge Design Document for DAB Review", icon: "fa-box-archive" }
    ];

    function App() {
      // Step Tracking: 1 = Input, 2 = SAVIA Recommendation, 3 = Agent Output
      const [step, setStep] = useState(1);

      const [workflowId, setWorkflowId] = useState(null);
      const [rawText, setRawText] = useState("");
      const [inputType, setInputType] = useState("txt");
      const [file, setFile] = useState(null);
      const [fileName, setFileName] = useState("");
      const [loading, setLoading] = useState(false);
      const [statusMsg, setStatusMsg] = useState("");

      const [recommendation, setRecommendation] = useState(null);
      const [selectedAgent, setSelectedAgent] = useState("mom");
      const [agentOutput, setAgentOutput] = useState(null);
      const [viewRawJson, setViewRawJson] = useState(false);

      // STEP 1: Process Input File / Text & Trigger SAVIA Recommendation
      const handleProcessInputAndRecommend = async () => {
        if (!rawText.trim() && !file) {
          alert("Please enter input text or upload a file (PDF, Word, TXT, Audio, Video).");
          return;
        }

        setLoading(true);
        setStatusMsg("Ingesting document and extracting content...");
        try {
          let currentWf = workflowId;
          let textToAnalyze = rawText;

          if (file) {
            const formData = new FormData();
            formData.append("file", file);
            const uploadRes = await fetch(`${API_BASE}/ingestion/upload`, {
              method: "POST",
              body: formData
            });
            const uploadData = await uploadRes.json();
            if (!uploadRes.ok) throw new Error(uploadData.detail || "Upload failed");
            
            currentWf = uploadData.workflow_id;
            setWorkflowId(currentWf);
            textToAnalyze = uploadData.full_normalized_text;
            setRawText(textToAnalyze);
          }

          setStatusMsg("SAVIA Orchestrator analyzing content...");
          const recRes = await fetch(`${API_BASE}/savia/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              workflow_id: currentWf,
              raw_text: textToAnalyze,
              input_type: inputType
            })
          });

          const recData = await recRes.json();
          if (!recRes.ok) throw new Error(recData.detail || "Recommendation failed");

          setRecommendation(recData);
          if (recData.primary_agent) {
            setSelectedAgent(recData.primary_agent);
          }
          
          setStep(2); // Move to Step 2: SAVIA Recommendation Layer
          setStatusMsg("SAVIA Recommendation generated successfully!");
        } catch (err) {
          alert("Error during ingestion/recommendation: " + err.message);
        } finally {
          setLoading(false);
        }
      };

      // STEP 2 -> STEP 3: Execute Selected/Recommended Agent
      const handleExecuteAgent = async (agentNameToRun) => {
        const targetAgent = agentNameToRun || selectedAgent;
        setLoading(true);
        setStatusMsg(`Executing ${targetAgent.toUpperCase()} Agent...`);
        try {
          const res = await fetch(`${API_BASE}/agents/${targetAgent}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              workflow_id: workflowId,
              input_text: rawText,
              bypass_approval: true
            })
          });
          const data = await res.json();
          if (!res.ok) throw new Error(data.detail || "Agent execution failed");

          setAgentOutput(data);
          setSelectedAgent(targetAgent);
          setStep(3); // Move to Step 3: Agent Output
          setStatusMsg(`${targetAgent.toUpperCase()} Agent execution complete!`);
        } catch (err) {
          alert(`Error executing agent: ` + err.message);
        } finally {
          setLoading(false);
        }
      };

      // Reset Workflow
      const handleReset = () => {
        setStep(1);
        setWorkflowId(null);
        setRawText("");
        setFile(null);
        setFileName("");
        setRecommendation(null);
        setAgentOutput(null);
        setStatusMsg("");
      };

      return (
        <div className="max-w-7xl mx-auto px-4 py-8 w-full space-y-8">
          
          {/* Header Banner */}
          <header className="glass rounded-2xl p-6 flex flex-col sm:flex-row justify-between items-center gap-4 border-b border-indigo-500/20 shadow-2xl">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-3xl font-extrabold text-white shadow-lg shadow-indigo-500/30">
                <i className="fa-solid fa-brain"></i>
              </div>
              <div>
                <h1 className="text-2xl font-black text-white tracking-wide">SAVIA Architecture Platform</h1>
                <p className="text-xs text-indigo-300 font-medium">AI-Powered SDLC Assistant & Enterprise Agent Orchestrator</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {workflowId && (
                <div className="bg-slate-900/90 px-4 py-2 rounded-xl border border-slate-800 text-xs">
                  <span className="text-slate-400">Workflow: </span>
                  <span className="font-mono text-indigo-400 font-bold">{workflowId}</span>
                </div>
              )}
              {step > 1 && (
                <button 
                  onClick={handleReset} 
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold py-2 px-3 rounded-xl transition"
                >
                  <i className="fa-solid fa-rotate-left mr-1"></i> New Session
                </button>
              )}
            </div>
          </header>

          {/* Stepper Process Bar */}
          <div className="grid grid-cols-3 gap-4">
            <div className={`p-4 rounded-xl border text-center transition ${step === 1 ? 'bg-indigo-950/70 border-indigo-500 text-indigo-200' : 'bg-slate-900/50 border-slate-800 text-slate-500'}`}>
              <span className="block text-xs font-bold uppercase tracking-wider mb-1">Step 1</span>
              <span className="text-sm font-extrabold"><i className="fa-solid fa-cloud-arrow-up mr-2"></i>Input Ingestion</span>
            </div>
            <div className={`p-4 rounded-xl border text-center transition ${step === 2 ? 'bg-indigo-950/70 border-indigo-500 text-indigo-200' : 'bg-slate-900/50 border-slate-800 text-slate-500'}`}>
              <span className="block text-xs font-bold uppercase tracking-wider mb-1">Step 2</span>
              <span className="text-sm font-extrabold"><i className="fa-solid fa-compass mr-2"></i>SAVIA Recommendation</span>
            </div>
            <div className={`p-4 rounded-xl border text-center transition ${step === 3 ? 'bg-indigo-950/70 border-indigo-500 text-indigo-200' : 'bg-slate-900/50 border-slate-800 text-slate-500'}`}>
              <span className="block text-xs font-bold uppercase tracking-wider mb-1">Step 3</span>
              <span className="text-sm font-extrabold"><i className="fa-solid fa-square-poll-vertical mr-2"></i>Agent Output</span>
            </div>
          </div>

          {/* STEP 1: INPUT INGESTION */}
          {step === 1 && (
            <div className="glass rounded-2xl p-8 space-y-6 animate-fade-in border border-slate-800">
              <div className="border-b border-slate-800 pb-4 flex justify-between items-center">
                <h2 className="text-lg font-extrabold text-white flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-sm">1</span>
                  Step 1: Input Ingestion
                </h2>
                <span className="text-xs text-slate-400">Word, PDF, DOCX, TXT, Audio, or Video</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Text input option */}
                <div className="space-y-3">
                  <label className="block text-xs font-bold text-slate-300 uppercase">Option A: Text / Requirement Input</label>
                  <textarea
                    rows="8"
                    value={rawText}
                    onChange={(e) => setRawText(e.target.value)}
                    placeholder="Enter meeting discussion transcript, business requirements, architectural spec, or user stories..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-4 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition"
                  ></textarea>
                </div>

                {/* File Upload option */}
                <div className="space-y-3 flex flex-col justify-between">
                  <div>
                    <label className="block text-xs font-bold text-slate-300 uppercase mb-3">Option B: File Upload (PDF, DOCX, TXT, Audio, Video)</label>
                    <div className="relative overflow-hidden border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-2xl p-6 text-center transition bg-slate-950/50 flex flex-col items-center justify-center min-h-[160px] cursor-pointer">
                      <i className="fa-solid fa-file-circle-plus text-4xl text-indigo-400 mb-2"></i>
                      <p className="text-xs text-slate-300 font-semibold mb-1">Click to select file or drag here</p>
                      <p className="text-[11px] text-slate-500">Supports .pdf, .docx, .txt, .mp3, .wav, .mp4</p>
                      <input 
                        type="file" 
                        onChange={(e) => {
                          const selected = e.target.files[0];
                          if (selected) {
                            setFile(selected);
                            setFileName(selected.name);
                            if (selected.name.match(/\.(mp3|wav|m4a)$/i)) setInputType("audio");
                            else if (selected.name.match(/\.(mp4|mov|avi)$/i)) setInputType("video");
                            else if (selected.name.match(/\.pdf$/i)) setInputType("pdf");
                            else if (selected.name.match(/\.docx?$/i)) setInputType("doc");
                            else setInputType("txt");
                          }
                        }}
                        className="opacity-0 absolute inset-0 cursor-pointer w-full h-full"
                      />
                    </div>
                    {fileName && (
                      <div className="mt-3 bg-indigo-950/60 text-indigo-300 border border-indigo-800 p-2.5 rounded-xl text-xs flex items-center justify-between">
                        <span className="font-semibold truncate"><i className="fa-solid fa-paperclip mr-2"></i>{fileName}</span>
                        <span className="text-[10px] uppercase font-bold bg-indigo-900 px-2 py-0.5 rounded">{inputType}</span>
                      </div>
                    )}
                  </div>

                  {/* Submit Button */}
                  <button
                    onClick={handleProcessInputAndRecommend}
                    disabled={loading}
                    className="relative z-20 w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-4 px-6 rounded-xl transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-3 text-sm mt-4 cursor-pointer"
                  >
                    {loading ? (
                      <>
                        <i className="fa-solid fa-spinner fa-spin text-lg"></i> Processing Input...
                      </>
                    ) : (
                      <>
                        <i className="fa-solid fa-paper-plane"></i> Process Input & Ask SAVIA
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 2: SAVIA RECOMMENDATION LAYER */}
          {step === 2 && recommendation && (
            <div className="glass rounded-2xl p-8 space-y-6 animate-fade-in border-2 border-indigo-500/40">
              <div className="border-b border-slate-800 pb-4 flex justify-between items-center">
                <h2 className="text-lg font-extrabold text-white flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-sm">2</span>
                  Step 2: SAVIA Orchestration & Recommendation Layer
                </h2>
                <span className="text-xs bg-indigo-900/80 text-indigo-300 px-3 py-1 rounded-full font-bold uppercase">
                  SAVIA Decision Engine
                </span>
              </div>

              {/* SAVIA Recommendation Banner */}
              <div className="bg-gradient-to-r from-indigo-950 via-slate-900 to-slate-950 p-6 rounded-2xl border border-indigo-500/30 space-y-4">
                <div className="flex items-center gap-3">
                  <i className="fa-solid fa-wand-magic-sparkles text-2xl text-indigo-400"></i>
                  <div>
                    <h3 className="text-base font-extrabold text-white">SAVIA Recommends: <span className="text-indigo-400 uppercase">{recommendation.primary_agent} AGENT</span></h3>
                    <p className="text-xs text-slate-300 mt-1">{recommendation.primary_reason}</p>
                  </div>
                </div>

                {/* Primary Action Button */}
                <div className="pt-2">
                  <button
                    onClick={() => handleExecuteAgent(recommendation.primary_agent)}
                    disabled={loading}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold py-4 px-6 rounded-xl transition shadow-lg shadow-emerald-600/30 flex items-center justify-center gap-3 text-base cursor-pointer"
                  >
                    {loading ? (
                      <><i className="fa-solid fa-spinner fa-spin"></i> Executing {recommendation.primary_agent.toUpperCase()} Agent...</>
                    ) : (
                      <><i className="fa-solid fa-circle-play text-xl"></i> Execute Recommended Agent ({recommendation.primary_agent.toUpperCase()})</>
                    )}
                  </button>
                </div>
              </div>

              {/* All 8 Enterprise Agents Grid */}
              <div className="space-y-3 pt-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Or Select & Execute Any SDLC Agent Manually:</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {ALL_AGENTS_CONFIG.map((ag) => {
                    const isRecommended = recommendation.primary_agent === ag.id;
                    return (
                      <button
                        key={ag.id}
                        onClick={() => handleExecuteAgent(ag.id)}
                        disabled={loading}
                        className={`p-4 rounded-xl text-left border transition flex flex-col justify-between space-y-2 cursor-pointer ${
                          isRecommended 
                            ? "bg-indigo-950/60 border-indigo-500 text-white ring-2 ring-indigo-500/50" 
                            : "bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700"
                        }`}
                      >
                        <div className="flex justify-between items-center">
                          <i className={`fa-solid ${ag.icon} text-lg ${isRecommended ? 'text-indigo-400' : 'text-slate-400'}`}></i>
                          {isRecommended && <span className="text-[10px] bg-indigo-600 text-white px-2 py-0.5 rounded font-extrabold uppercase">Recommended</span>}
                        </div>
                        <div>
                          <div className="font-extrabold text-sm">{ag.name}</div>
                          <div className="text-[11px] text-slate-400 mt-1">{ag.desc}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: AGENT OUTPUT DISPLAY */}
          {step === 3 && agentOutput && (
            <div className="glass rounded-2xl p-8 space-y-6 animate-fade-in border border-emerald-500/40">
              <div className="border-b border-slate-800 pb-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center text-sm font-bold">3</span>
                  <div>
                    <h2 className="text-lg font-extrabold text-white uppercase tracking-wide">
                      Step 3: {agentOutput.agent_name.toUpperCase()} Output
                    </h2>
                    <p className="text-xs text-slate-400">Artifact ID: {agentOutput.artifact_id} · Stage: {agentOutput.stage}</p>
                  </div>
                </div>

                <div className="flex gap-2">
                  <button 
                    onClick={() => setViewRawJson(!viewRawJson)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold py-2 px-3 rounded-xl transition"
                  >
                    <i className="fa-solid fa-code mr-1"></i> {viewRawJson ? "Visual View" : "Raw JSON"}
                  </button>
                  <button 
                    onClick={() => setStep(2)} 
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2 px-3 rounded-xl transition"
                  >
                    <i className="fa-solid fa-arrow-left mr-1"></i> Back to Recommendation
                  </button>
                </div>
              </div>

              {/* View Raw JSON Toggle */}
              {viewRawJson ? (
                <div className="bg-slate-950 p-6 rounded-2xl border border-slate-800 text-xs font-mono overflow-x-auto max-h-[550px]">
                  <pre className="text-emerald-400 leading-relaxed">{JSON.stringify(agentOutput.content, null, 2)}</pre>
                </div>
              ) : (
                /* VISUAL RICH CARDS FOR AGENTS */
                <div className="space-y-6">
                  
                  {/* MOM AGENT VISUAL OUTPUT */}
                  {agentOutput.agent_name === "mom" && (
                    <div className="space-y-6">
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-2">
                        <h3 className="text-sm font-extrabold text-indigo-400 uppercase flex items-center gap-2">
                          <i className="fa-solid fa-file-lines"></i> Executive Summary & Minutes
                        </h3>
                        <p className="text-sm text-slate-200 leading-relaxed">
                          {agentOutput.content.summary || agentOutput.content.discussion_summary || "Executive summary generated from meeting content."}
                        </p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {agentOutput.content.key_points && agentOutput.content.key_points.length > 0 && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-emerald-400 uppercase flex items-center gap-2">
                              <i className="fa-solid fa-list"></i> Key Points Discussed
                            </h4>
                            <ul className="space-y-2 text-xs text-slate-300">
                              {agentOutput.content.key_points.map((kp, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <i className="fa-solid fa-check text-emerald-500 mt-0.5"></i>
                                  <span>{kp}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {agentOutput.content.requirements_identified && agentOutput.content.requirements_identified.length > 0 && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-cyan-400 uppercase flex items-center gap-2">
                              <i className="fa-solid fa-lightbulb"></i> Requirements Identified
                            </h4>
                            <ul className="space-y-2 text-xs text-slate-300">
                              {agentOutput.content.requirements_identified.map((req, idx) => (
                                <li key={idx} className="flex items-start gap-2">
                                  <i className="fa-solid fa-circle-notch text-cyan-400 mt-0.5"></i>
                                  <span>{req}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {agentOutput.content.decisions && agentOutput.content.decisions.length > 0 && (
                        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                          <h4 className="text-xs font-extrabold text-amber-400 uppercase flex items-center gap-2">
                            <i className="fa-solid fa-gavel"></i> Key Decisions Finalized
                          </h4>
                          <div className="grid grid-cols-1 gap-2">
                            {agentOutput.content.decisions.map((dec, idx) => (
                              <div key={idx} className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-xs flex justify-between items-center">
                                <span className="font-semibold text-slate-200">{typeof dec === 'object' ? dec.decision : dec}</span>
                                <span className="text-[10px] bg-amber-950 text-amber-300 px-2 py-0.5 rounded font-bold uppercase">Decision</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {agentOutput.content.action_items && agentOutput.content.action_items.length > 0 && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-emerald-400 uppercase flex items-center gap-2">
                            <i className="fa-solid fa-tasks"></i> Action Items & Follow-ups
                          </h4>
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs text-slate-300 border-collapse">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                                  <th className="py-2.5 px-3">ID</th>
                                  <th className="py-2.5 px-3">Action Description</th>
                                  <th className="py-2.5 px-3">Assignee</th>
                                  <th className="py-2.5 px-3">Due Date</th>
                                  <th className="py-2.5 px-3">Priority</th>
                                </tr>
                              </thead>
                              <tbody>
                                {agentOutput.content.action_items.map((act, idx) => (
                                  <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/40">
                                    <td className="py-2.5 px-3 font-mono text-indigo-400 font-bold">{act.action_id || `ACT-${idx+1}`}</td>
                                    <td className="py-2.5 px-3 font-semibold text-slate-200">{act.action || act}</td>
                                    <td className="py-2.5 px-3 text-slate-400">{act.assignee || "Not specified"}</td>
                                    <td className="py-2.5 px-3 text-slate-400">{act.due_date || "Not specified"}</td>
                                    <td className="py-2.5 px-3">
                                      <span className="bg-emerald-950 text-emerald-300 text-[10px] px-2 py-0.5 rounded font-bold">{act.priority || "Medium"}</span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* READINESS SCORING & AUDIT VISUAL OUTPUT WITH SDLC CYCLE JUSTIFICATION */}
                  {agentOutput.agent_name === "readiness-scoring" && (
                    <div className="space-y-6">
                      {/* Overall Score Banner */}
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                          <h3 className="text-base font-extrabold text-white">{agentOutput.content.title}</h3>
                          <p className="text-xs text-slate-400 mt-1">Rubric: {agentOutput.content.audit_rubric}</p>
                        </div>
                        <div className="text-left md:text-right bg-slate-950 px-5 py-3 rounded-2xl border border-slate-800">
                          <span className={`text-4xl font-black ${agentOutput.content.overall_score >= 80 ? 'text-emerald-400' : (agentOutput.content.overall_score >= 60 ? 'text-amber-400' : 'text-rose-400')}`}>
                            {agentOutput.content.overall_score}/100
                          </span>
                          <p className="text-[11px] text-slate-300 font-bold mt-0.5">{agentOutput.content.grade}</p>
                        </div>
                      </div>

                      {/* SDLC Cycle Score Justification Breakdown Section */}
                      {agentOutput.content.sdlc_score_justification && (
                        <div className="bg-gradient-to-b from-slate-900 to-slate-950 p-6 rounded-2xl border border-indigo-500/30 space-y-6">
                          <div className="border-b border-slate-800 pb-3">
                            <h4 className="text-sm font-extrabold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                              <i className="fa-solid fa-chart-line"></i> SDLC Cycle Score Justification Breakdown
                            </h4>
                            <p className="text-xs text-slate-300 mt-2 leading-relaxed">
                              {agentOutput.content.sdlc_score_justification.overall_summary}
                            </p>
                          </div>

                          {/* 5 SDLC Stages Justification Grid */}
                          <div className="space-y-4">
                            <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Detailed SDLC Lifecycle Justification:</h5>
                            <div className="grid grid-cols-1 gap-4">
                              {agentOutput.content.sdlc_score_justification.sdlc_stage_breakdown && 
                               agentOutput.content.sdlc_score_justification.sdlc_stage_breakdown.map((stg, idx) => (
                                <div key={idx} className="bg-slate-900/90 p-5 rounded-xl border border-slate-800 space-y-3">
                                  <div className="flex justify-between items-center">
                                    <span className="font-extrabold text-sm text-white">{stg.sdlc_stage}</span>
                                    <div className="flex items-center gap-2">
                                      <span className={`text-xs font-mono font-bold ${stg.stage_score >= 80 ? 'text-emerald-400' : (stg.stage_score >= 60 ? 'text-amber-400' : 'text-rose-400')}`}>
                                        Score: {stg.stage_score}%
                                      </span>
                                      <span className={`text-[10px] px-2.5 py-0.5 rounded font-bold uppercase ${stg.status === 'Pass' ? 'bg-emerald-950 text-emerald-300' : (stg.status === 'Needs Attention' ? 'bg-amber-950 text-amber-300' : 'bg-rose-950 text-rose-300')}`}>
                                        {stg.status}
                                      </span>
                                    </div>
                                  </div>

                                  <p className="text-xs text-slate-300 leading-relaxed">
                                    <strong>Score Justification:</strong> {stg.justification}
                                  </p>

                                  {stg.key_deficits && stg.key_deficits.length > 0 && (
                                    <div className="bg-slate-950 p-3 rounded-lg border border-slate-800/80 text-xs space-y-1">
                                      <span className="text-[11px] font-bold text-rose-400 uppercase block">Key Deficits Identified:</span>
                                      <ul className="list-disc list-inside text-slate-400 text-[11px]">
                                        {stg.key_deficits.map((def, dIdx) => (
                                          <li key={dIdx}>{def}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}

                                  {stg.remediation_action && (
                                    <div className="text-[11px] text-emerald-300 bg-emerald-950/40 p-2.5 rounded-lg border border-emerald-900/50 flex items-start gap-2">
                                      <i className="fa-solid fa-wrench text-emerald-400 mt-0.5"></i>
                                      <span><strong>Remediation Action:</strong> {stg.remediation_action}</span>
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Dimension Scores Grid */}
                      {agentOutput.content.dimensions && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {agentOutput.content.dimensions.map((dim, idx) => (
                            <div key={idx} className="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-2">
                              <div className="flex justify-between items-center">
                                <span className="font-bold text-xs text-slate-200">{dim.name}</span>
                                <span className="text-xs font-bold text-indigo-400">{dim.score}%</span>
                              </div>
                              <p className="text-[11px] text-slate-400">{dim.summary}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* AGILE USER STORIES & BACKLOG EPICS VISUAL OUTPUT */}
                  {agentOutput.agent_name === "user-stories" && (
                    <div className="space-y-6">
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div>
                          <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                            <i className="fa-solid fa-list-check text-indigo-400"></i> Agile User Stories & Backlog Epics
                          </h3>
                          <div className="flex flex-wrap gap-2 mt-2">
                            <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded font-bold uppercase">Epics:</span>
                            {(agentOutput.content.epics || []).map((ep, idx) => (
                              <span key={idx} className="text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 px-2.5 py-0.5 rounded-full font-semibold">
                                {ep}
                              </span>
                            ))}
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            const stories = agentOutput.content.user_stories || [];
                            const headers = ["User Story ID", "Epic", "Title", "As A", "I Want", "So That", "Story Points", "Priority"];
                            const rows = stories.map(s => [
                              `"${s.user_story_id || ''}"`,
                              `"${(s.epic || '').replace(/"/g, '""')}"`,
                              `"${(s.title || '').replace(/"/g, '""')}"`,
                              `"${(s.as_a || '').replace(/"/g, '""')}"`,
                              `"${(s.i_want || '').replace(/"/g, '""')}"`,
                              `"${(s.so_that || '').replace(/"/g, '""')}"`,
                              `"${s.story_points || 3}"`,
                              `"${s.priority || 'Medium'}"`
                            ]);
                            const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
                            const encodedUri = encodeURI(csvContent);
                            const link = document.createElement("a");
                            link.setAttribute("href", encodedUri);
                            link.setAttribute("download", `Agile_User_Stories_Export.csv`);
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                          }}
                          className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold py-2.5 px-4 rounded-xl transition flex items-center gap-2 cursor-pointer shadow-lg shadow-emerald-600/20"
                        >
                          <i className="fa-solid fa-file-export"></i> Export to CSV / JIRA / Azure DevOps
                        </button>
                      </div>

                      <div className="grid grid-cols-1 gap-4">
                        {(agentOutput.content.user_stories || []).map((st, idx) => (
                          <div key={idx} className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-4">
                            <div className="flex flex-wrap justify-between items-center gap-2 border-b border-slate-800/80 pb-3">
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-bold bg-indigo-950 text-indigo-400 border border-indigo-800 px-2.5 py-1 rounded-lg">
                                  {st.user_story_id || `US-${idx+1}`}
                                </span>
                                <span className="text-xs font-bold text-slate-400">[{st.epic || 'Core'}]</span>
                                <h4 className="font-extrabold text-sm text-white">{st.title}</h4>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] bg-slate-800 text-emerald-400 font-mono font-bold px-2.5 py-0.5 rounded">
                                  {st.story_points || 3} Story Pts
                                </span>
                                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${st.priority === 'High' ? 'bg-rose-950 text-rose-300' : 'bg-amber-950 text-amber-300'}`}>
                                  {st.priority || 'Medium'}
                                </span>
                              </div>
                            </div>

                            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs text-slate-300 space-y-1">
                              <p><strong>As a:</strong> <span className="text-indigo-300">{st.as_a || 'User'}</span></p>
                              <p><strong>I want to:</strong> <span className="text-slate-200">{st.i_want || st.description}</span></p>
                              <p><strong>So that:</strong> <span className="text-emerald-300">{st.so_that || 'Business goal achieved.'}</span></p>
                            </div>

                            {st.acceptance_criteria && st.acceptance_criteria.length > 0 && (
                              <div className="space-y-2">
                                <h5 className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider">BDD Acceptance Criteria (Given / When / Then):</h5>
                                <div className="space-y-2">
                                  {st.acceptance_criteria.map((ac, acIdx) => (
                                    <div key={acIdx} className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
                                      <p className="text-slate-400"><strong className="text-amber-400">GIVEN:</strong> {ac.given}</p>
                                      <p className="text-slate-400"><strong className="text-cyan-400">WHEN:</strong> {ac.when}</p>
                                      <p className="text-slate-400"><strong className="text-emerald-400">THEN:</strong> {ac.then}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* REQUIREMENT GAP ANALYSIS & RTM VISUAL OUTPUT */}
                  {agentOutput.agent_name === "gap-analysis" && (
                    <div className="space-y-6">
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-2">
                        <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                          <i className="fa-solid fa-magnifying-glass text-cyan-400"></i> {agentOutput.content.title}
                        </h3>
                        <p className="text-xs text-slate-300 leading-relaxed">{agentOutput.content.summary}</p>
                      </div>

                      {/* RTM Traceability Matrix Table */}
                      {agentOutput.content.traceability_matrix && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-network-wired"></i> End-to-End Requirements Traceability Matrix (RTM)
                          </h4>
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs text-slate-300 border-collapse">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                                  <th className="py-2.5 px-3">Req ID</th>
                                  <th className="py-2.5 px-3">Business Objective</th>
                                  <th className="py-2.5 px-3">Requirement</th>
                                  <th className="py-2.5 px-3">User Story</th>
                                  <th className="py-2.5 px-3">Tech Component</th>
                                  <th className="py-2.5 px-3">Test Case</th>
                                  <th className="py-2.5 px-3">Status</th>
                                </tr>
                              </thead>
                              <tbody>
                                {agentOutput.content.traceability_matrix.map((rt, idx) => (
                                  <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/40">
                                    <td className="py-2.5 px-3 font-mono font-bold text-cyan-400">{rt.req_id}</td>
                                    <td className="py-2.5 px-3 text-slate-300">{rt.business_objective}</td>
                                    <td className="py-2.5 px-3 text-slate-200 font-medium">{rt.requirement_description}</td>
                                    <td className="py-2.5 px-3 font-mono text-indigo-300">{rt.user_story_id}</td>
                                    <td className="py-2.5 px-3 text-slate-400">{rt.technical_component}</td>
                                    <td className="py-2.5 px-3 font-mono text-amber-300">{rt.test_case_id}</td>
                                    <td className="py-2.5 px-3">
                                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${rt.status === 'Fully Covered' ? 'bg-emerald-950 text-emerald-300' : 'bg-rose-950 text-rose-300'}`}>
                                        {rt.status}
                                      </span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Standard vs Custom Gaps & Unmet Requirements */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {agentOutput.content.gap_classification && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                              <i className="fa-solid fa-code-fork"></i> Standard vs Custom Gap Classification
                            </h4>
                            <div className="space-y-3">
                              {agentOutput.content.gap_classification.map((gp, idx) => (
                                <div key={idx} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs space-y-1">
                                  <div className="flex justify-between items-center">
                                    <span className="font-bold text-slate-200">{gp.feature_area}</span>
                                    <span className="text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded font-bold">
                                      {gp.gap_type}
                                    </span>
                                  </div>
                                  <p className="text-slate-400">{gp.description}</p>
                                  <p className="text-emerald-400 text-[11px]"><strong>Rec:</strong> {gp.recommendation}</p>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {agentOutput.content.unmet_requirements_and_impact && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-rose-400 uppercase tracking-wider flex items-center gap-2">
                              <i className="fa-solid fa-triangle-exclamation"></i> Unmet Requirements & Timeline/Budget Impact
                            </h4>
                            <div className="space-y-3">
                              {agentOutput.content.unmet_requirements_and_impact.map((um, idx) => (
                                <div key={idx} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs space-y-2">
                                  <div className="flex justify-between items-center">
                                    <span className="font-mono text-rose-400 font-bold">{um.unmet_req_id}</span>
                                    <span className="text-[10px] bg-rose-950 text-rose-300 px-2 py-0.5 rounded font-bold uppercase">
                                      Risk: {um.risk_level}
                                    </span>
                                  </div>
                                  <p className="text-slate-300 font-medium">{um.description}</p>
                                  <div className="flex justify-between text-[11px] bg-slate-900 p-2 rounded-lg border border-slate-800">
                                    <span className="text-amber-300"><i className="fa-solid fa-clock mr-1"></i> +{um.timeline_impact_weeks} Wks</span>
                                    <span className="text-emerald-300"><i className="fa-solid fa-dollar-sign mr-1"></i> {um.budget_impact_effort}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* CHANGE IMPACT ASSESSMENT & INTERDEPENDENCY MATRIX VISUAL OUTPUT */}
                  {agentOutput.agent_name === "change-impact" && (
                    <div className="space-y-6">
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-2">
                        <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                          <i className="fa-solid fa-arrows-split-up-and-left text-amber-400"></i> {agentOutput.content.title}
                        </h3>
                        <p className="text-xs text-slate-300 leading-relaxed">{agentOutput.content.executive_summary}</p>
                      </div>

                      {/* Cross Platform & Operational Readiness */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {agentOutput.content.cross_platform_impact_analysis && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                              <i className="fa-solid fa-arrows-rotate"></i> Cross-Platform Impact Analysis
                            </h4>
                            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
                              <p><strong className="text-slate-400">Current Legacy:</strong> <span className="text-slate-200">{agentOutput.content.cross_platform_impact_analysis.current_platform_state}</span></p>
                              <p><strong className="text-cyan-400">Target Architecture:</strong> <span className="text-slate-200">{agentOutput.content.cross_platform_impact_analysis.target_architecture_state}</span></p>
                              <span className="inline-block text-[10px] bg-amber-950 text-amber-300 px-2 py-0.5 rounded font-bold uppercase mt-1">
                                Impact Level: {agentOutput.content.cross_platform_impact_analysis.impact_level}
                              </span>
                            </div>
                          </div>
                        )}

                        {agentOutput.content.operational_readiness_evaluation && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                              <i className="fa-solid fa-shield-halved"></i> Operational Readiness Evaluation
                            </h4>
                            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
                              <div className="flex justify-between items-center">
                                <span className="text-slate-400 font-bold">Cutover Strategy:</span>
                                <span className="text-emerald-400 font-bold">{agentOutput.content.operational_readiness_evaluation.cutover_strategy}</span>
                              </div>
                              <p><strong className="text-slate-400">Rollback Protocol:</strong> <span className="text-slate-200">{agentOutput.content.operational_readiness_evaluation.rollback_protocol}</span></p>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Interdependency Matrix Table */}
                      {agentOutput.content.interdependency_matrix && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-table-cells"></i> Interdependency Matrix
                          </h4>
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs text-slate-300 border-collapse">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                                  <th className="py-2.5 px-3">Component</th>
                                  <th className="py-2.5 px-3">Depends On</th>
                                  <th className="py-2.5 px-3">Impacted By</th>
                                  <th className="py-2.5 px-3">Criticality</th>
                                </tr>
                              </thead>
                              <tbody>
                                {agentOutput.content.interdependency_matrix.map((mx, idx) => (
                                  <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/40">
                                    <td className="py-2.5 px-3 font-bold text-white">{mx.component}</td>
                                    <td className="py-2.5 px-3 text-slate-400">{(mx.depends_on || []).join(", ")}</td>
                                    <td className="py-2.5 px-3 text-slate-400">{(mx.impacted_by || []).join(", ")}</td>
                                    <td className="py-2.5 px-3">
                                      <span className="bg-rose-950 text-rose-300 text-[10px] px-2 py-0.5 rounded font-bold">{mx.criticality || 'High'}</span>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* KDD PACKAGE FOR DAB VISUAL OUTPUT */}
                  {agentOutput.agent_name === "kdd-package" && (
                    <div className="space-y-6">
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-2">
                        <div className="flex justify-between items-center">
                          <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                            <i className="fa-solid fa-box text-amber-400"></i> {agentOutput.content.title}
                          </h3>
                          <span className="font-mono text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-3 py-1 rounded-lg font-bold">
                            {agentOutput.content.dab_submission_id || 'DAB-KDD-001'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">{agentOutput.content.executive_dossier}</p>
                      </div>

                      {/* Decision Making Framework ADRs */}
                      {agentOutput.content.decision_making_framework && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-scale-balanced"></i> Architectural Decision-Making Framework (ADR)
                          </h4>
                          <div className="grid grid-cols-1 gap-4">
                            {agentOutput.content.decision_making_framework.map((adr, idx) => (
                              <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
                                <div className="flex justify-between items-center">
                                  <span className="font-mono text-indigo-400 font-bold">{adr.decision_id || `ADR-00${idx+1}`} - {adr.decision_title}</span>
                                  <span className="text-[10px] bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded font-bold uppercase">
                                    DAB Rec: {adr.dab_review_recommendation || 'Approve'}
                                  </span>
                                </div>
                                <p className="text-slate-300"><strong>Rationale:</strong> {adr.solution_rationale}</p>
                                {adr.alternatives_considered && (
                                  <p className="text-slate-400 text-[11px]"><strong>Alternatives Considered:</strong> {adr.alternatives_considered.join(", ")}</p>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Enterprise Compliance and Audit */}
                      {agentOutput.content.enterprise_compliance_and_audit && (
                        <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                          <h4 className="text-xs font-extrabold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-certificate"></i> Enterprise Compliance & Governance Audit
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                              <span className="text-slate-400 block text-[10px] font-bold uppercase">GxP Audit Readiness</span>
                              <span className="text-emerald-400 font-extrabold">{agentOutput.content.enterprise_compliance_and_audit.gxp_audit_readiness}</span>
                            </div>
                            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                              <span className="text-slate-400 block text-[10px] font-bold uppercase">Data Sovereignty</span>
                              <span className="text-indigo-400 font-extrabold">{agentOutput.content.enterprise_compliance_and_audit.data_sovereignty}</span>
                            </div>
                            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                              <span className="text-slate-400 block text-[10px] font-bold uppercase">Disaster Recovery</span>
                              <span className="text-amber-400 font-extrabold">{agentOutput.content.enterprise_compliance_and_audit.disaster_recovery_rto_rpo}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* DDL3 DESIGN VISUAL OUTPUT */}
                  {agentOutput.agent_name === "ddl3" && (
                    <div className="space-y-6">
                      {/* Title & Purpose Header */}
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-3">
                        <div className="flex justify-between items-center">
                          <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                            <i className="fa-solid fa-cubes text-indigo-400"></i> {agentOutput.content.title || "DDL3 Detailed Design Specification"}
                          </h3>
                          <span className="font-mono text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-3 py-1 rounded-lg font-bold">
                            {agentOutput.content.design_id || 'DES-001'}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">
                          <strong>Purpose & Background:</strong> {agentOutput.content.purpose || agentOutput.content.summary || "Comprehensive Functional and Technical DDL3 Specification."}
                        </p>
                        {agentOutput.content.scope && (
                          <p className="text-xs text-slate-400">
                            <strong>Scope & Boundaries:</strong> {agentOutput.content.scope}
                          </p>
                        )}
                      </div>

                      {/* WRIEF Components Classification */}
                      {agentOutput.content.wrief_classification && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-layer-group"></i> WRIEF Components Classification (Workflow, Report, Interface, Extension, Form)
                          </h4>
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
                            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                              <span className="text-[10px] font-bold text-amber-400 uppercase block">Workflows (W)</span>
                              <ul className="text-slate-300 space-y-1 text-[11px]">
                                {(agentOutput.content.wrief_classification.workflows || ["Standard Workflow"]).map((item, idx) => (
                                  <li key={idx} className="flex items-center gap-1.5"><i className="fa-solid fa-diagram-next text-amber-500 text-[9px]"></i>{item}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                              <span className="text-[10px] font-bold text-cyan-400 uppercase block">Reports (R)</span>
                              <ul className="text-slate-300 space-y-1 text-[11px]">
                                {(agentOutput.content.wrief_classification.reports || ["Standard Report"]).map((item, idx) => (
                                  <li key={idx} className="flex items-center gap-1.5"><i className="fa-solid fa-chart-pie text-cyan-400 text-[9px]"></i>{item}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                              <span className="text-[10px] font-bold text-emerald-400 uppercase block">Interfaces (I)</span>
                              <ul className="text-slate-300 space-y-1 text-[11px]">
                                {(agentOutput.content.wrief_classification.interfaces || ["REST Interface"]).map((item, idx) => (
                                  <li key={idx} className="flex items-center gap-1.5"><i className="fa-solid fa-plug text-emerald-400 text-[9px]"></i>{item}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                              <span className="text-[10px] font-bold text-purple-400 uppercase block">Extensions (E)</span>
                              <ul className="text-slate-300 space-y-1 text-[11px]">
                                {(agentOutput.content.wrief_classification.extensions || ["Custom Hook"]).map((item, idx) => (
                                  <li key={idx} className="flex items-center gap-1.5"><i className="fa-solid fa-puzzle-piece text-purple-400 text-[9px]"></i>{item}</li>
                                ))}
                              </ul>
                            </div>

                            <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
                              <span className="text-[10px] font-bold text-rose-400 uppercase block">Forms (F)</span>
                              <ul className="text-slate-300 space-y-1 text-[11px]">
                                {(agentOutput.content.wrief_classification.forms || ["Standard Layout"]).map((item, idx) => (
                                  <li key={idx} className="flex items-center gap-1.5"><i className="fa-solid fa-file-invoice text-rose-400 text-[9px]"></i>{item}</li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Process Flow & Architecture */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {agentOutput.content.process_flow && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                              <i className="fa-solid fa-bars-staggered"></i> Process Execution Flow
                            </h4>
                            <ol className="space-y-2 text-xs text-slate-300">
                              {agentOutput.content.process_flow.map((step, idx) => (
                                <li key={idx} className="flex items-start gap-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                                  <span className="font-bold text-cyan-400 font-mono text-xs">{idx + 1}.</span>
                                  <span>{step}</span>
                                </li>
                              ))}
                            </ol>
                          </div>
                        )}

                        {agentOutput.content.architecture && (
                          <div className="bg-slate-900/90 p-5 rounded-2xl border border-slate-800 space-y-3">
                            <h4 className="text-xs font-extrabold text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                              <i className="fa-solid fa-sitemap"></i> Architecture & Technical Pattern
                            </h4>
                            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 text-xs space-y-2">
                              <p><strong>Pattern:</strong> <span className="text-emerald-300 font-bold">{agentOutput.content.architecture.pattern || 'Microservices'}</span></p>
                              <div>
                                <strong className="text-slate-400 block mb-1">Components:</strong>
                                <div className="flex flex-wrap gap-1.5">
                                  {(agentOutput.content.architecture.components || []).map((comp, cIdx) => (
                                    <span key={cIdx} className="bg-slate-900 text-indigo-300 border border-slate-800 px-2 py-0.5 rounded text-[11px] font-mono">
                                      {comp}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Functional Requirements Traceability Grid */}
                      {agentOutput.content.functional_requirements && agentOutput.content.functional_requirements.length > 0 && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-list-check"></i> Functional Requirements Traceability
                          </h4>
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs text-slate-300 border-collapse">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                                  <th className="py-2.5 px-3">Req ID</th>
                                  <th className="py-2.5 px-3">Traceability</th>
                                  <th className="py-2.5 px-3">Requirement Description</th>
                                </tr>
                              </thead>
                              <tbody>
                                {agentOutput.content.functional_requirements.map((freq, idx) => (
                                  <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/40">
                                    <td className="py-2.5 px-3 font-mono font-bold text-amber-400">{freq.req_id || `REQ-${idx+1}`}</td>
                                    <td className="py-2.5 px-3 font-mono text-indigo-300">{freq.user_story_id || freq.traceability || "US-001"}</td>
                                    <td className="py-2.5 px-3 text-slate-200">{freq.description || freq}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Configuration Parameters DDL3 */}
                      {agentOutput.content.configuration_parameters && agentOutput.content.configuration_parameters.length > 0 && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-gears"></i> Configuration Parameters & Setup
                          </h4>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                            {agentOutput.content.configuration_parameters.map((param, idx) => (
                              <div key={idx} className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
                                <div className="flex justify-between items-center">
                                  <span className="font-mono text-cyan-300 font-bold">{param.param}</span>
                                  <span className="text-[10px] bg-slate-900 text-slate-400 px-2 py-0.5 rounded font-mono">{param.default || 'Default'}</span>
                                </div>
                                <p className="text-slate-400 text-[11px]">{param.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* TEST AGENT VISUAL OUTPUT */}
                  {agentOutput.agent_name === "test" && (
                    <div className="space-y-6">
                      <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-3">
                        <div className="flex justify-between items-center">
                          <h3 className="text-base font-extrabold text-white flex items-center gap-2">
                            <i className="fa-solid fa-vial text-rose-500"></i> FIT / UAT Test Inventory & Scenario Stitching
                          </h3>
                          <span className="text-xs bg-rose-950 text-rose-300 border border-rose-800 px-3 py-1 rounded-lg font-bold">
                            End-to-End Test Automation
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed">
                          {agentOutput.content.summary || "Automates end-to-end test creation, generating FIT/UAT inventories, manual test cases, and orchestrated test plans."}
                        </p>

                        {/* Interactive Buttons matching Image 2 */}
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                          <button onClick={() => alert("Test Case Generation Active: " + (agentOutput.content.test_cases?.length || 0) + " cases created")} className="bg-slate-950 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold py-2.5 px-3 rounded-xl transition flex items-center gap-2 cursor-pointer">
                            <i className="fa-solid fa-arrow-up-right-from-square text-rose-500"></i> Testing Agent Demo - Test Case Generation
                          </button>
                          <button onClick={() => alert("FIT/UAT Inventory Active: " + (agentOutput.content.test_inventory?.length || 0) + " items inventory")} className="bg-slate-950 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold py-2.5 px-3 rounded-xl transition flex items-center gap-2 cursor-pointer">
                            <i className="fa-solid fa-arrow-up-right-from-square text-rose-500"></i> Testing Agent Demo - Test Case Inventory
                          </button>
                          <button onClick={() => alert("Scenario Stitching Test Plan Active: " + (agentOutput.content.test_plan?.title || 'Active'))} className="bg-slate-950 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-bold py-2.5 px-3 rounded-xl transition flex items-center gap-2 cursor-pointer">
                            <i className="fa-solid fa-arrow-up-right-from-square text-rose-500"></i> Testing Agent User Guide
                          </button>
                        </div>
                      </div>

                      {/* FIT / UAT Inventory */}
                      {agentOutput.content.test_inventory && agentOutput.content.test_inventory.length > 0 && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-rose-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-boxes-stacked"></i> FIT and UAT Test Case Inventory
                          </h4>
                          <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs text-slate-300 border-collapse">
                              <thead>
                                <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px]">
                                  <th className="py-2.5 px-3">Inventory ID</th>
                                  <th className="py-2.5 px-3">Type</th>
                                  <th className="py-2.5 px-3">Category</th>
                                  <th className="py-2.5 px-3">Description</th>
                                  <th className="py-2.5 px-3">Traceability</th>
                                </tr>
                              </thead>
                              <tbody>
                                {agentOutput.content.test_inventory.map((inv, idx) => (
                                  <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/40">
                                    <td className="py-2.5 px-3 font-mono font-bold text-rose-400">{inv.inventory_id || `INV-${idx+1}`}</td>
                                    <td className="py-2.5 px-3 font-bold text-slate-200">{inv.type}</td>
                                    <td className="py-2.5 px-3 text-slate-300">{inv.category}</td>
                                    <td className="py-2.5 px-3 text-slate-300">{inv.description}</td>
                                    <td className="py-2.5 px-3 font-mono text-indigo-300">{inv.traceability}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {/* Manual Test Cases */}
                      {agentOutput.content.test_cases && agentOutput.content.test_cases.length > 0 && (
                        <div className="bg-slate-900/90 p-6 rounded-2xl border border-slate-800 space-y-4">
                          <h4 className="text-xs font-extrabold text-cyan-400 uppercase tracking-wider flex items-center gap-2">
                            <i className="fa-solid fa-list-check"></i> Manual Test Cases & Execution Steps
                          </h4>
                          <div className="space-y-4">
                            {agentOutput.content.test_cases.map((tc, idx) => (
                              <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-3">
                                <div className="flex justify-between items-center border-b border-slate-800 pb-2">
                                  <div className="flex items-center gap-2">
                                    <span className="font-mono font-bold text-rose-400 text-xs">{tc.test_case_id || `TC-00${idx+1}`}</span>
                                    <span className="font-extrabold text-slate-200">{tc.title}</span>
                                  </div>
                                  <span className="text-[10px] bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded font-bold uppercase">{tc.type || 'UAT'}</span>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-400 text-[11px]">
                                  <p><strong>Preconditions:</strong> {(tc.preconditions || []).join(", ")}</p>
                                  <p><strong>Expected Result:</strong> <span className="text-emerald-300">{tc.expected_result}</span></p>
                                </div>
                                {tc.test_steps && (
                                  <div className="space-y-1">
                                    <strong className="text-[11px] text-amber-400 uppercase block">Execution Steps:</strong>
                                    <ol className="list-decimal list-inside text-slate-300 text-[11px] space-y-0.5">
                                      {tc.test_steps.map((st, sIdx) => (
                                        <li key={sIdx}>{st}</li>
                                      ))}
                                    </ol>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                </div>
              )}
            </div>
          )}

          {/* Footer Status Bar */}
          <footer className="glass rounded-xl p-3 flex justify-between items-center text-xs text-slate-400">
            <span className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              SAVIA Platform Status: Active
            </span>
            <span>{statusMsg || "Ready"}</span>
          </footer>

        </div>
      );
    }

    ReactDOM.render(<App />, document.getElementById("root"));
  