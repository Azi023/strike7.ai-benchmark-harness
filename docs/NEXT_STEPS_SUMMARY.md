# Strike7 - Next Steps Summary

**Date:** 2026-01-23
**Current Status:** Phase 6C Complete, Phase 7 Partially Started
**Focus:** Fix UX Issues → Add Metrics → MCP Integration (Later)

---

## 🎯 Immediate Priority: Fix UX Issues (Option C Completion)

### Problems Identified

From the screenshots you provided:
1. ❌ **Flag submission not working** - Input field not accepting input
2. ❌ **No access URL visible** - Users don't know where to test (http://localhost:PORT)
3. ❌ **Missing validation** - No checks for flag format
4. ❌ **Poor UX flow** - Users confused about what to do after starting

### Solution: Comprehensive UX Fix

**Prompt for Antigravity:**
```
Read and implement everything in this file:
/home/atheeque/workspace/strike7-benchmarks/ANTIGRAVITY_PROMPT_UX_FIXES.md

This is a comprehensive specification for fixing critical UX issues in the Strike7 dashboard. Focus on:

Priority 1 (Critical):
- Fix flag submission so users can actually type and submit flags
- Add prominent "Access Benchmark" section showing http://localhost:PORT
- Add copy URL and open in browser buttons

Priority 2 (Important):
- Add flag format validation (S7BEN{...})
- Support numeric flags like S7BEN{123456}
- Add proper error messages
- Add success/failure notifications (toast messages)

Priority 3 (Nice to have):
- Enhance details modal with testing instructions
- Add runtime counter that updates live
- Add better button state management

Files to modify:
- dashboard/static/js/dashboard.js (main fixes)
- dashboard/static/css/dashboard.css (new styles)
- dashboard/templates/index.html (HTML structure)

Test with benchmark S7BEN-EASY-002 (Hardcoded Secrets - simplest to verify).
```

**Why This Matters:**
Human testing is essential for ranking benchmarks. Without a good UX, researchers can't effectively test and provide feedback.

**Expected Outcome:**
After these fixes, a user should be able to:
1. Click "Start Container"
2. Immediately see "Access at: http://localhost:5000" with copy/open buttons
3. Test the vulnerability
4. Click "Submit Flag" and easily enter the captured flag
5. See clear success/failure message

---

## 📊 Next: Add Evaluation Metrics (Option B)

After UX is fixed, implement the metrics system.

### What to Build

**File:** `dashboard/api/evaluation_metrics.py`

**Core Metrics:**

1. **pass@k** - Can the agent solve this at all?
   - Formula: `1 - (1 - success_rate)^k`
   - Use case: "Did the agent succeed at least once in k tries?"

2. **pass^k** - Is the agent reliable?
   - Formula: `success_rate^k`
   - Use case: "Does the agent succeed every time?"

3. **Time-to-Flag (TTF)** - How fast?
   - Track: Seconds from container start to flag capture
   - Use case: Measure efficiency

4. **Efficiency Score** - How optimal was the approach?
   - Formula: `min_requests / actual_requests`
   - Use case: Did agent use optimal path or brute force?

5. **Stealth Score** - How detectable was the attack?
   - Factors: WAF blocks, rate limits, error count
   - Score: 0-100 (100 = perfect stealth)

### API Endpoints to Add

```
GET  /api/metrics/pass-at-k?benchmark_id=X&k=5
GET  /api/metrics/ttf?benchmark_id=X
GET  /api/metrics/efficiency?benchmark_id=X
GET  /api/metrics/leaderboard
POST /api/metrics/record-trial
```

### Implementation Checklist

```
□ Create evaluation_metrics.py module
□ Implement pass@k calculation
□ Implement pass^k calculation
□ Implement TTF tracking
□ Implement efficiency scoring
□ Implement stealth scoring
□ Add /api/metrics endpoint
□ Update session tracker to record metrics
□ Add metrics to leaderboard
□ Document metrics API
```

**Time Estimate:** 3-5 hours

---

## 🔌 Later: MCP Integration (Option A)

**Note:** You mentioned this seems complicated - that's fine! Do this last after the other two are working.

### Why MCP is Lower Priority Right Now

1. **UX is broken** - Fix what users see first
2. **No metrics yet** - Can't measure agent performance without metrics
3. **MCP is advanced** - Requires Claude Desktop setup and testing

### When to Come Back to MCP

After:
- ✅ UX issues fixed (users can test manually)
- ✅ Metrics implemented (can measure performance)
- ✅ Both working well together

Then:
- Set up Claude Desktop with MCP config
- Test basic tool calls
- Iterate based on what you learn

**The MCP server is already built** - You just need to test it when ready.

---

## 🗂️ Files Created Today

| File | Purpose | Status |
|------|---------|--------|
| `ANTIGRAVITY_PROMPT_UX_FIXES.md` | Complete UX fix specification | ✅ Ready |
| `ANTIGRAVITY_PROMPT_UI_BUTTONS.md` | Original button implementation | ✅ Done |
| `PHASE7_KICKOFF.md` | Phase 7 roadmap | ✅ Done |
| `MCP_QUICKSTART.md` | MCP setup guide | ✅ Done |
| `dashboard/mcp_server_minimal.py` | MCP server prototype | ✅ Built |
| `test_mcp_server.sh` | MCP test suite | ✅ Done |
| `API_FIX_SUMMARY.md` | Container API fixes | ✅ Done |

---

## 📋 Recommended Task Order

### Week 1: UX Fixes (This Week)
```
Day 1-2: Give Antigravity the UX fix prompt
Day 2-3: Test and iterate on fixes
Day 3-4: Verify all benchmarks work correctly
```

**Success Criteria:**
- [ ] Flag submission works on all benchmarks
- [ ] Access URL is clearly visible when running
- [ ] Copy URL button works
- [ ] Open in browser button works
- [ ] Validation catches invalid flags
- [ ] Error messages are helpful
- [ ] Users are never confused about what to do

### Week 2: Metrics Implementation
```
Day 1-2: Create evaluation_metrics.py
Day 2-3: Implement core calculations (pass@k, TTF)
Day 3-4: Add API endpoints
Day 4-5: Test and document
```

**Success Criteria:**
- [ ] pass@k calculation works
- [ ] TTF tracking works
- [ ] Metrics API endpoints return correct data
- [ ] Leaderboard shows metrics
- [ ] Documentation updated

### Week 3+: MCP Integration (When Ready)
```
Day 1: Set up Claude Desktop
Day 2: Test basic MCP tools
Day 3: Test end-to-end workflow
Day 4-5: Iterate and refine
```

**Success Criteria:**
- [ ] Claude can list benchmarks
- [ ] Claude can start containers
- [ ] Claude can submit flags
- [ ] Claude can check status
- [ ] Full workflow works end-to-end

---

## 🎯 Current Sprint Goals

**This Week's Focus:**
1. ✅ Fix flag submission (CRITICAL)
2. ✅ Add access URL display (CRITICAL)
3. ✅ Add validation and error handling
4. ✅ Test with real benchmarks

**Success Metric:**
A security researcher can:
- Start any benchmark
- Immediately see where to access it
- Test the vulnerability manually
- Submit the flag easily
- Get clear feedback

**When Done:**
- UX feels professional and polished
- No user confusion
- Ready for external testers

---

## 📝 Quick Reference

### Give Antigravity This Prompt:

```
Read and implement the UX fixes in:
/home/atheeque/workspace/strike7-benchmarks/ANTIGRAVITY_PROMPT_UX_FIXES.md

Focus on these critical issues:
1. Fix flag submission input field
2. Add prominent access URL display (http://localhost:PORT)
3. Add copy URL and open in browser buttons
4. Add validation for flag format
5. Add proper error notifications

Test with S7BEN-EASY-002 first (port 5000).
```

### Test After Antigravity's Changes:

```bash
# 1. Start dashboard
python dashboard/app.py

# 2. Open browser
http://localhost:5500

# 3. Test workflow:
- Click "Start" on S7BEN-EASY-002
- Verify you see "Access at: http://localhost:5000"
- Click "Open in Browser" button
- Get the flag from the benchmark
- Click "Submit Flag"
- Type: S7BEN{h4rdc0d3d_s3cr3ts_4r3_b4d}
- Verify success message appears
- Click "Stop"
```

---

## 🚀 What's Working Now

### ✅ Backend (Phase 6C)
- Container management APIs
- Flag validation APIs
- Session tracking APIs
- Safety features
- All endpoints tested and working

### ⚠️ Frontend (Partial)
- Buttons exist but UX needs fixes
- Flag submission broken
- No access URL display
- Missing validation

### 📊 Metrics (Not Started)
- Need to implement
- Next priority after UX

### 🔌 MCP (Prototype Built)
- Server exists but untested
- Low priority for now
- Do last

---

## 💡 Key Insights

### Why This Order?

1. **UX First**: Users can't test without good UX
2. **Metrics Second**: Can't measure what you can't use
3. **MCP Last**: Advanced feature, needs stable foundation

### What's Most Important?

**For Humans**: Good UX for manual testing
**For AI Agents**: Metrics to measure performance
**For Integration**: MCP protocol (later)

### What's the Goal?

Create a professional benchmark testing platform where:
- Researchers can easily test vulnerabilities
- We can measure and compare agent performance
- AI agents can eventually automate testing

---

## 📚 Documentation

- **UX Fix Spec**: `ANTIGRAVITY_PROMPT_UX_FIXES.md`
- **API Docs**: `dashboard/API_DOCUMENTATION.md`
- **Quick Start**: `dashboard/QUICKSTART_API.md`
- **Phase 7 Plan**: `PHASE7_KICKOFF.md`
- **MCP Guide**: `MCP_QUICKSTART.md`

---

## ❓ Questions?

**Q: Should I do MCP first?**
A: No - fix UX first so humans can test. MCP can wait.

**Q: How long will UX fixes take?**
A: If Antigravity does it: 1-2 hours. Then test: 1 hour. Total: 2-3 hours.

**Q: When should I do metrics?**
A: After UX is working and tested.

**Q: What if Antigravity doesn't fix everything?**
A: The spec is comprehensive. If something doesn't work, point it to the specific section.

---

**Status:** Ready to proceed with UX fixes ✅
**Next Action:** Give Antigravity the UX fix prompt
**ETA:** UX fixes complete in 2-3 hours, then metrics in 3-5 hours

---

**Document Version:** 1.0
**Created:** 2026-01-23
**For:** UX Fixes → Metrics → MCP (in that order)
