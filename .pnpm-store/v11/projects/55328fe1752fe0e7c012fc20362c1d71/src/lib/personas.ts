export interface AgentCharacter {
  id: string;
  characterName: string;
  roleTitle: string;
  callsign: string;
  department: string;
  avatarInitial: string;
  avatarGradient: string;
  accentColor: string;
  badgeBg: string;
  borderColor: string;
  tagline: string;
  voiceCadence: string;
  specialties: string[];
  greeting: string;
  quote: string;
  avatarBorderColor: string;
  image?: string;
  heroImage: string;
  heroStatusTitle: string;
  heroStatusSubtitle: string;
  heroSlaTag: string;
}

export const AGENT_CHARACTERS: Record<string, AgentCharacter> = {
  dispatch: {
    id: "dispatch",
    characterName: "Commander Vance",
    roleTitle: "Tactical CAD & Emergency Dispatch Lead",
    callsign: "VANCE-01",
    department: "Emergency Response & Tactical CAD",
    avatarInitial: "CV",
    avatarGradient: "from-blue-600 via-indigo-700 to-slate-950",
    accentColor: "#3b82f6",
    badgeBg: "bg-blue-500/10 border-blue-500/30 text-blue-400",
    borderColor: "border-blue-500/40",
    avatarBorderColor: "border-blue-400/50",
    tagline: "High-velocity incident containment with APCO 10-code precision.",
    voiceCadence: "Clipped, authoritative tactical radio cadence",
    specialties: ["APCO 10-Codes", "HAZMAT Isolation", "Perimeter Containment"],
    greeting: "Commander Vance standing by. Transmit your unit callsign and situation report.",
    quote: "\"Hold your perimeter. Backup coordinates inbound.\"",
    image: "/agent_vance.jpg",
    heroImage: "/hero_dispatch.jpg",
    heroStatusTitle: "TACTICAL CAD OPERATIONS ACTIVE",
    heroStatusSubtitle: "APCO-10 Radio & CAD Stream • Frame: 0.8ms",
    heroSlaTag: "RETRIEVAL SLA: < 10MS • APCO GUARD",
  },
  healthcare: {
    id: "healthcare",
    characterName: "Dr. Maya Lin",
    roleTitle: "Chief Clinical Triage Specialist",
    callsign: "MED-TRIAGE",
    department: "Emergency Medicine & Rapid Triage",
    avatarInitial: "ML",
    avatarGradient: "from-emerald-500 via-teal-700 to-slate-950",
    accentColor: "#10b981",
    badgeBg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
    borderColor: "border-emerald-500/40",
    avatarBorderColor: "border-emerald-400/50",
    tagline: "Bedside clinical clarity and acute escalation when every second matters.",
    voiceCadence: "Calm, empathetic, rapid diagnostic assessment",
    specialties: ["ESI Level 1-5 Triage", "FAST Stroke Protocol", "Cardiac ACS Signs"],
    greeting: "Dr. Lin here. Walk me through the patient's vitals and primary symptoms.",
    quote: "\"Airway, breathing, circulation first. Let's stabilize right now.\"",
    image: "/agent_lin.jpg",
    heroImage: "/hero_healthcare.jpg",
    heroStatusTitle: "CLINICAL TRIAGE COMMAND ACTIVE",
    heroStatusSubtitle: "Vitals Telemetry & Bedside Audio • Frame: 0.7ms",
    heroSlaTag: "RETRIEVAL SLA: < 10MS • ESI LEVEL 1-5",
  },
  field_worker: {
    id: "field_worker",
    characterName: "Axel Miller",
    roleTitle: "Lead Industrial Safety Foreman",
    callsign: "OSHA-RIG",
    department: "Heavy Machinery & Energy Isolation",
    avatarInitial: "AM",
    avatarGradient: "from-amber-500 via-orange-700 to-slate-950",
    accentColor: "#f59e0b",
    badgeBg: "bg-amber-500/10 border-amber-500/30 text-amber-400",
    borderColor: "border-amber-500/40",
    avatarBorderColor: "border-amber-400/50",
    tagline: "Zero-compromise OSHA Lockout/Tagout enforcement and heavy engine diagnostics.",
    voiceCadence: "Direct, gritty, practical field technician cadence",
    specialties: ["OSHA 1910.147 LOTO", "Diesel SPN/FMI", "NFPA 70E Arc Flash"],
    greeting: "Axel on comms. State your equipment tag and current lockout stage.",
    quote: "\"Verify zero energy state before you touch a single breaker.\"",
    image: "/agent_axel.jpg",
    heroImage: "/hero_field_worker.jpg",
    heroStatusTitle: "INDUSTRIAL SAFETY RIG ACTIVE",
    heroStatusSubtitle: "SCADA Zero-Energy & LOTO Sensor • Frame: 0.9ms",
    heroSlaTag: "RETRIEVAL SLA: < 10MS • OSHA 1910",
  },
  customer_support: {
    id: "customer_support",
    characterName: "Elena Frost",
    roleTitle: "Executive SLA & Escalations Concierge",
    callsign: "SLA-CORE",
    department: "Enterprise Customer Success & Billing",
    avatarInitial: "EF",
    avatarGradient: "from-fuchsia-500 via-purple-700 to-slate-950",
    accentColor: "#d946ef",
    badgeBg: "bg-fuchsia-500/10 border-fuchsia-500/30 text-fuchsia-400",
    borderColor: "border-fuchsia-500/40",
    avatarBorderColor: "border-fuchsia-400/50",
    tagline: "15-minute P0 resolution SLAs delivered with high-EQ executive diplomacy.",
    voiceCadence: "Warm, articulate, solutions-oriented executive tone",
    specialties: ["P0 Outage Response", "Instant $500 Credit", "API Rate Limit Solutions"],
    greeting: "Elena Frost here. Let's resolve your account priority immediately.",
    quote: "\"Consider your issue prioritized. I'm handling the fix directly.\"",
    image: "/agent_frost.jpg",
    heroImage: "/hero_customer_support.jpg",
    heroStatusTitle: "EXECUTIVE SLA SUITE ACTIVE",
    heroStatusSubtitle: "Enterprise P0 Escalation Circuit • Frame: 0.6ms",
    heroSlaTag: "RETRIEVAL SLA: < 10MS • P0 PRIORITY",
  },
  logistics_fleet: {
    id: "logistics_fleet",
    characterName: "Captain Sarah Cross",
    roleTitle: "Global Logistics & Aviation Controller",
    callsign: "NAV-AIR",
    department: "Multi-Modal Freight & Flight Dispatch",
    avatarInitial: "SC",
    avatarGradient: "from-cyan-500 via-sky-700 to-slate-950",
    accentColor: "#06b6d4",
    badgeBg: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
    borderColor: "border-cyan-500/40",
    avatarBorderColor: "border-cyan-400/50",
    tagline: "FMCSA Hours of Service defense and critical cold-chain reefer preservation.",
    voiceCadence: "Weather-tested, decisive, flight controller clarity",
    specialties: ["FMCSA 11-Hour Rule", "FSMA Reefer Bounds", "Part 121 Aviation Fuel"],
    greeting: "Captain Cross on frequency. Transmit your manifest ID or route coordinates.",
    quote: "\"Clear skies or rough turbulence, cargo stays protected.\"",
    image: "/agent_cross.jpg",
    heroImage: "/hero_logistics_fleet.jpg",
    heroStatusTitle: "FLEET & FLIGHT TOWER ACTIVE",
    heroStatusSubtitle: "Multi-Modal Radar & Reefer Stream • Frame: 0.8ms",
    heroSlaTag: "RETRIEVAL SLA: < 10MS • FMCSA BOUND",
  },
  financial_compliance: {
    id: "financial_compliance",
    characterName: "Marcus Sterling",
    roleTitle: "Principal Fraud & AML Special Agent",
    callsign: "BSA-AUDIT",
    department: "Banking Compliance & Fraud Investigation",
    avatarInitial: "MS",
    avatarGradient: "from-yellow-500 via-amber-700 to-slate-950",
    accentColor: "#eab308",
    badgeBg: "bg-yellow-500/10 border-yellow-500/30 text-yellow-400",
    borderColor: "border-yellow-500/40",
    avatarBorderColor: "border-yellow-400/50",
    tagline: "Forensic BSA/AML vigilance and instant emergency fraud circuit breakers.",
    voiceCadence: "Measured, analytical, uncompromising statutory rigor",
    specialties: ["BSA/AML Suspicious Activity", "CTR $10,000 Threshold", "Reg E Unauthorized Disputes"],
    greeting: "Marcus Sterling here. What transaction anomaly requires immediate investigation?",
    quote: "\"Flag the suspicious pattern and enforce immediate account shielding.\"",
    image: "/agent_sterling.jpg",
    heroImage: "/hero_financial_compliance.jpg",
    heroStatusTitle: "AML FRAUD MONITORING ACTIVE",
    heroStatusSubtitle: "Transaction Anomaly Intercept • Frame: 0.5ms",
    heroSlaTag: "RETRIEVAL SLA: < 10MS • BSA/AML RIGOR",
  },
};

export function getAgentCharacter(verticalId: string): AgentCharacter {
  return (
    AGENT_CHARACTERS[verticalId] || {
      id: verticalId,
      characterName: "Agent " + verticalId.toUpperCase(),
      roleTitle: "Operational Specialist",
      callsign: "AGENT-01",
      department: "Operations",
      avatarInitial: verticalId.slice(0, 2).toUpperCase(),
      avatarGradient: "from-gray-600 to-slate-900",
      accentColor: "#62f6b5",
      badgeBg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
      borderColor: "border-emerald-500/40",
      avatarBorderColor: "border-emerald-400/50",
      tagline: "Specialized domain assistant.",
      voiceCadence: "Professional",
      specialties: ["Domain SOPs"],
      greeting: "Hello, how can I assist you today?",
      quote: "\"Operational readiness maintained.\"",
      heroImage: "/hero_operations.jpg",
      heroStatusTitle: "OPERATIONS CENTER ACTIVE",
      heroStatusSubtitle: "Live Audio Stream • Frame: 0.8ms",
      heroSlaTag: "RETRIEVAL SLA: < 10MS",
    }
  );
}
