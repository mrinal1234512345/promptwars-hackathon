"use client";

import { useState } from "react";
import {
  ArrowRight,
  BarChart3,
  BookOpen,
  BrainCircuit,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  Code2,
  Compass,
  Flame,
  Layers3,
  Menu,
  Play,
  Sparkles,
  Target,
  X,
} from "lucide-react";

const roadmap = [
  { title: "Modern JavaScript foundations", detail: "Variables, async patterns, modules", progress: 82, color: "mint" },
  { title: "React interface architecture", detail: "Components, state, data fetching", progress: 46, color: "purple" },
  { title: "Build a production dashboard", detail: "Your hands-on capstone project", progress: 0, color: "amber" },
];

const skills = [
  { name: "JavaScript", score: 86, tone: "mint" },
  { name: "React", score: 64, tone: "purple" },
  { name: "TypeScript", score: 42, tone: "amber" },
  { name: "Testing", score: 28, tone: "rose" },
];

export default function Home() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [showPlan, setShowPlan] = useState(false);

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#" aria-label="Pathfinder home">
          <span className="brand-mark"><Compass size={18} /></span>
          <span>pathfinder<span className="brand-dot">.</span></span>
        </a>
        <nav className={menuOpen ? "nav-links nav-open" : "nav-links"}>
          <a href="#journey">My journey</a>
          <a href="#skills">Skills</a>
          <a href="#mentor">AI mentor</a>
          <a href="#about">How it works</a>
        </nav>
        <div className="header-actions">
          <button className="avatar" aria-label="Open profile">AK</button>
          <button className="menu-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      <section className="hero shell">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={15} /> Your learning, made personal</div>
          <h1>Build the career<br /><em>you actually want.</em></h1>
          <p>Pathfinder turns your ambitions into a clear, adaptive learning journey. Know what to learn next, why it matters, and when you&apos;re ready.</p>
          <div className="hero-actions">
            <button className="button button-dark" onClick={() => setShowPlan(true)}>Continue your journey <ArrowRight size={17} /></button>
            <a className="text-link" href="#about">See how it works <ChevronRight size={15} /></a>
          </div>
          <div className="social-proof"><div className="faces"><span>SM</span><span>JR</span><span>NT</span><span>+</span></div><span>Join 12,000+ curious builders</span></div>
        </div>
        <div className="hero-orbit">
          <div className="orbit orbit-one"></div><div className="orbit orbit-two"></div>
          <div className="hero-card main-orb">
            <div className="orb-icon"><BrainCircuit size={25} /></div>
            <span className="orb-label">Your next best step</span>
            <strong>React interface<br />architecture</strong>
            <span className="orb-meta"><Clock3 size={13} /> 4h 20m · Module 2 of 6</span>
            <div className="orb-progress"><span></span></div>
          </div>
          <div className="floating-card floating-top"><Target size={17} /><span><b>64%</b><small>ready for your role</small></span></div>
          <div className="floating-card floating-bottom"><Flame size={17} /><span><b>7 day streak</b><small>keep the momentum</small></span></div>
        </div>
      </section>

      <section className="stats-strip"><div className="shell stats-grid"><div><strong>82%</strong><span>of learners stay on track</span></div><div><strong>3.4×</strong><span>faster skill progression</span></div><div><strong>12k+</strong><span>people finding their path</span></div><div className="stats-note"><Sparkles size={17} /> Built around <b>your</b> goals</div></div></section>

      <section className="dashboard shell" id="journey">
        <div className="section-heading"><div><div className="eyebrow">Good morning, Alex</div><h2>Make progress that <em>feels good.</em></h2></div><button className="icon-button" aria-label="Get help"><CircleHelp size={20} /></button></div>
        <div className="dashboard-grid">
          <div className="panel roadmap-panel">
            <div className="panel-heading"><div><span className="panel-kicker"><BookOpen size={14} /> Your roadmap</span><h3>Frontend engineer</h3></div><span className="status-pill">On track</span></div>
            <div className="roadmap-list">{roadmap.map((item, index) => <div className="roadmap-item" key={item.title}><div className={`step-number ${index === 0 ? "done" : ""}`}>{index === 0 ? <Check size={14} /> : index + 1}</div><div className="roadmap-content"><div className="roadmap-title"><b>{item.title}</b><span>{item.progress ? `${item.progress}%` : "Up next"}</span></div><small>{item.detail}</small><div className="progress-track"><span className={`progress-${item.color}`} style={{ width: `${item.progress}%` }} /></div></div></div>)}</div>
            <button className="panel-link" onClick={() => setShowPlan(true)}>View full roadmap <ArrowRight size={15} /></button>
          </div>
          <div className="panel readiness-panel" id="skills">
            <div className="panel-heading"><div><span className="panel-kicker"><BarChart3 size={14} /> Skill snapshot</span><h3>Readiness score</h3></div><span className="readiness-score">64<span>/100</span></span></div>
            <div className="skill-bars">{skills.map((skill) => <div className="skill-row" key={skill.name}><div><span>{skill.name}</span><b>{skill.score}%</b></div><div className="progress-track"><span className={`progress-${skill.tone}`} style={{ width: `${skill.score}%` }} /></div></div>)}</div>
            <button className="panel-link" onClick={() => setShowPlan(true)}>See your skill gaps <ArrowRight size={15} /></button>
          </div>
        </div>
      </section>

      <section className="mentor-section" id="mentor"><div className="shell mentor-content"><div className="mentor-icon"><Sparkles size={25} /></div><div><div className="eyebrow">Your AI mentor</div><h2>Never wonder <em>what&apos;s next.</em></h2><p>Get unstuck, understand the why behind every recommendation, and turn confusion into your next small win.</p></div><button className="button button-light" onClick={() => setShowPlan(true)}>Talk to your mentor <ArrowRight size={17} /></button></div></section>

      <section className="features shell" id="about"><div className="section-heading centered"><div><div className="eyebrow">A better way forward</div><h2>Designed for your <em>real life.</em></h2></div></div><div className="feature-grid"><div className="feature-card"><div className="feature-icon mint-icon"><Layers3 size={20} /></div><h3>One clear path</h3><p>No more scattered tabs or generic checklists. Everything you need, sequenced around your goals.</p></div><div className="feature-card"><div className="feature-icon purple-icon"><BrainCircuit size={20} /></div><h3>Adapts as you grow</h3><p>Your plan gets smarter with every assessment, project, and question you ask.</p></div><div className="feature-card"><div className="feature-icon amber-icon"><Code2 size={20} /></div><h3>Learn by doing</h3><p>Build meaningful projects that prove your skills and give your portfolio a pulse.</p></div></div></section>

      <footer className="footer shell"><a className="brand" href="#"><span className="brand-mark"><Compass size={18} /></span><span>pathfinder<span className="brand-dot">.</span></span></a><span>Made for people who are going places.</span><span>© 2025 Pathfinder</span></footer>

      {showPlan && <div className="modal-backdrop" onClick={() => setShowPlan(false)}><div className="modal" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setShowPlan(false)} aria-label="Close"><X size={19} /></button><div className="modal-spark"><Sparkles size={23} /></div><h2>Your path is ready.</h2><p>This website is set up as your personalized learning home. Connect your profile to generate a roadmap tailored to your target role.</p><button className="button button-dark modal-button" onClick={() => setShowPlan(false)}>Start with your profile <ArrowRight size={17} /></button></div></div>}
    </main>
  );
}
