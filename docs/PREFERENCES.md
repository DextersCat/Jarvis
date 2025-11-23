# AI Agent Preferences & Guidelines
**Owner:** Chairman Spencer  
**For:** Nexus, Astra, and all AI agents working in JARVIS workspace  
**Purpose:** Persistent preferences across chat sessions  
**Status:** Living document - update as preferences evolve

---

## 🎯 Session Start Protocol

**Every new AI agent session MUST:**
1. Read `docs/WORKSPACE-DIRECTORY-GUIDE.md` first (system knowledge)
2. Read this file second (user preferences)
3. Acknowledge understanding before proceeding

---

## 💬 Communication Preferences

### Style
- **Brief and direct** - no unnecessary introductions or conclusions
- **No emojis** unless explicitly requested
- **Factual updates** - avoid phrases like "Here's what I found:" or "The result is:"
- **Concise responses** - 1-3 sentences for simple answers when possible

### Tool Usage
- **Never announce tool names** to user (e.g., don't say "I'll use run_in_terminal")
- **Parallel operations** when possible (read multiple files at once)
- **Explain impact** for system-modifying commands

---

## 🔧 Technical Preferences

### Code Style
- **No code markers** like `(...existing code...)` or `// ... rest of code`
- **Full context** in replacements - include 3-5 lines before/after
- **Complete code** always - never placeholder comments
- **Preserve whitespace** exactly when editing

### File Organization
- **Documentation:** ALL `.md` files go in `docs/` folder (except README.md)
- **Tests:** Keep test files together
- **Configs:** Keep in `config/` or `core/` subdirectories
- **AI Models:** Heavy AI models MUST live under `F:\JARVIS_MODELS\` by default
- **Long-term Data:** Jarvis vault and archives go in `F:\JARVIS_VAULT\`
- **E:\ Drive:** NEVER use E:\ for anything - it is personal storage, off-limits to Jarvis

### Development Workflow
1. **Always activate venv on AI-Pi:** `source ~/jarvis_terminal_env/bin/activate`
2. **Use test files as reference:** test_g4_tasks.py is most recent and verified working
3. **Import pattern (AI-Pi):** `sys.path.insert(0, '/home/spencer/jarvis_terminal')` then direct imports
4. **Test before claiming success** - verify with actual execution when possible

---

## 🚫 Critical Rules

### DO NOT:
- ❌ Create new markdown documentation files without request
- ❌ Edit files without understanding full context
- ❌ Use `from core.*` imports without ensuring core/ package exists
- ❌ Assume packages are installed - verify first
- ❌ Run commands without venv activation on AI-Pi
- ❌ Make structural changes without confirmation
- ❌ Batch completion updates - mark todos complete immediately after finishing
- ❌ **Invent new architectures** - always choose Mode A (AI-Pi solo) or Mode B (distributed) explicitly based on instructions
- ❌ **Use E:\ drive** for anything - it is personal storage, completely off-limits to Jarvis

### ALWAYS:
- ✅ Read existing test files to understand patterns
- ✅ Check for errors after file edits (`get_errors` tool)
- ✅ Verify critical operations succeeded
- ✅ Update WORKSPACE-DIRECTORY-GUIDE.md after major changes
- ✅ Use most recent test files as reference (test_g4 > test_g1)
- ✅ Preserve existing working code and data

---

## 📊 Project Context

### Current Focus
- **Phase G5:** Voice Mode operational (mic + TTS)
- **Architecture:** Standalone AI-Pi (may migrate to distributed later)
- **Status:** All Phase G engines (G1-G4) tested and working

### Past Issues to Avoid
1. **Import errors:** Created files with wrong import paths (fixed: must use sys.path.insert)
2. **Missing core/ package:** Files expected core/ subdirectory that didn't exist (fixed: created core/)
3. **Missing dependencies:** PortAudio, dateparser not installed (fixed: installed via apt/pip)
4. **Background mode errors:** Started interactive programs in background (fixed: use -t flag for ssh)

### Quality Standards
- **Zero tolerance** for deviations from previous working state
- **Verify before claiming** - test with actual execution
- **Trust but verify** - check your own work
- **Working code is canonical** - test files show correct patterns
- **DOCUMENT IMMEDIATELY** when systems are verified working - do NOT wait until end of session
- **NEVER assume infrastructure doesn't exist** - always check/verify first

---

## ⚠️ CRITICAL: Session Crash Protection

### Documentation Timing (MANDATORY)
1. **Update WORKSPACE-DIRECTORY-GUIDE.md IMMEDIATELY** when you confirm something works
2. **Do NOT batch documentation updates** - write after each verification
3. **Do NOT assume** - verify by running commands/checking files
4. **Mark systems as VERIFIED WORKING** with timestamps in docs

### Crash Recovery Protocol
If chat crashes, next agent MUST:
1. Read WORKSPACE-DIRECTORY-GUIDE.md first
2. Look for "VERIFIED WORKING" timestamps
3. Trust documented working states
4. Resume from last verified checkpoint

**Reason:** 9-hour data loss on 2025-11-18 due to undocumented working systems

---

## 🎯 Priorities

### High Priority
1. System stability and reliability
2. Data preservation (ChromaDB, vault, configurations)
3. Accurate documentation
4. Cost efficiency (parallel operations, minimal API calls)

### Medium Priority
1. Performance optimization
2. Feature completeness
3. Code organization

### Low Priority
1. Cosmetic improvements
2. Experimental features

---

## 🔄 Workflow Preferences

### For Complex Tasks
1. **Use todo lists** - track progress with manage_todo_list tool
2. **Mark in-progress** before starting work
3. **Mark completed immediately** after finishing (not batched)
4. **Break down** into logical, actionable steps

### For File Operations
1. **Read first** - understand existing code before editing
2. **Test after** - verify edits didn't break functionality
3. **Preserve structure** - maintain existing patterns
4. **Batch edits** - use multi_replace when doing multiple independent changes

### For Research
1. **Check existing docs first** before searching
2. **Use canonical sources** - test files, working code
3. **Verify claims** with actual file reads
4. **Document findings** in appropriate files

---

## 🗂️ File Handling

### Critical Files (Extra Care)
- `voice_session.py` - Main voice mode entrypoint
- `action_engine.py` - Core orchestration
- `memory_engine.py` - ChromaDB interface
- `test_g4_tasks.py` - Most recent verified working test
- `WORKSPACE-DIRECTORY-GUIDE.md` - System knowledge anchor

### Backup Before Modifying
- Any file in `jarvis_terminal/` on AI-Pi
- ChromaDB data in `jarvis_memory/`
- Configuration files (`.env`, `config.py`)

---

## 📝 Documentation Standards

### When to Document
- **Major milestones** (Phase completions)
- **Architecture changes** (new systems, integrations)
- **Critical fixes** (bugs that broke functionality)
- **Performance improvements** (measured optimizations)

### When NOT to Document
- Minor edits or typo fixes
- Routine maintenance
- Temporary experimental work
- Unless explicitly requested

### Documentation Format
- **Clear titles** describing purpose
- **Date and status** at top
- **Concise summaries** before details
- **Code examples** when relevant
- **Update existing docs** rather than creating new ones when possible

---

## 🤝 Collaboration Notes

### Working with Astra AI
- Astra handles strategic planning and architecture decisions
- Nexus handles implementation and technical execution
- Both agents should read this file for consistency

### Handoff Protocol
- Document current state clearly
- Note any in-progress work
- Flag known issues or blockers
- Reference relevant files for context

---

## 💡 Lessons Learned (Update as we go)

### 2025-11-18
- Import pattern on AI-Pi MUST include sys.path.insert(0, '/home/spencer/jarvis_terminal')
- Test files (especially test_g4) are canonical reference for correct patterns
- Background mode wrong for interactive programs - use ssh -t
- All .md files should be in docs/ folder for organization
- **CRITICAL:** PC Brain Server exists at `~/JARVIS/api/websocket_server/server.py` in Ubuntu WSL2 and WORKS
- **CRITICAL:** Launch script `.\launch-ubuntu-jarvis.ps1` successfully starts server on port 8765
- **CRITICAL:** GPU Whisper (medium.en, CUDA, float16) loads and runs on RTX 5070 Ti
- **NEVER ASSUME** infrastructure doesn't exist - 9-hour loss from false "blocker" report

### (Add more as we encounter them)

---

## 🔐 Security & Credentials

### API Keys
- Stored in `~/.jarvis_tokens/.env` on AI-Pi
- Never log or display in output
- Verify existence before running API-dependent code

### OAuth Tokens
- Gmail: `gmail_token.json` (not yet configured)
- Calendar: `calendar_token.json` (not yet configured)
- Will require browser OAuth flow when setting up

---

## 📞 When in Doubt

1. **Read the docs** - WORKSPACE-DIRECTORY-GUIDE.md has the answers
2. **Check test files** - they show the correct way
3. **Ask for clarification** - better than breaking things
4. **Preserve working state** - don't fix what isn't broken

---

**Last Updated:** November 18, 2025  
**Next Review:** As needed when preferences change  
**Maintained By:** Chairman Spencer + AI agents (collaborative)
