const capabilities = [
  { n: "01", title: "Guided patient history", text: "A patient-friendly flow for sharing symptoms and medical history through touch, text, and supported speech." },
  { n: "02", title: "Medical document understanding", text: "A structured way to organize information from prescriptions, laboratory reports, and discharge summaries." },
  { n: "03", title: "Clinician-reviewed summary", text: "A clear draft that preserves sources and uncertainty for a qualified clinician to review and correct." },
];
export default function Home() {
  return <main className="shell">
    <header className="topbar"><a className="brand" href="/" aria-label="MediTalk home"><span className="mark">MT</span><span>MediTalk</span></a><span className="status">Development foundation</span></header>
    <section className="hero"><p className="eyebrow">PATIENT HISTORY, MADE CLEARER</p><h1>A better conversation.<br/>A clearer clinical history.</h1><p className="intro">MediTalk is being built to help patients share their history and help clinicians review organized, source-aware information.</p><div className="notice"><span className="dot"/><p>Foundation stage: patient intake, document processing, and clinical review workflows are not implemented yet.</p></div></section>
    <section className="features"><p className="eyebrow">PRODUCT DIRECTION</p><h2>One connected patient-to-clinician workflow</h2><div className="grid">{capabilities.map(c=><article className="card" key={c.n}><span className="number">{c.n}</span><h3>{c.title}</h3><p>{c.text}</p><span className="planned">Planned capability</span></article>)}</div></section>
    <footer>MediTalk supports clinical preparation. It does not replace professional medical judgment.</footer>
  </main>;
}
