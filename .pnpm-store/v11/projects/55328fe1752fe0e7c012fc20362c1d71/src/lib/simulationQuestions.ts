export interface CallerQuestion {
  id: string;
  category: string;
  prompt: string;
  shortTitle: string;
}

export const CALLER_QUESTIONS: Record<string, CallerQuestion[]> = {
  dispatch: [
    {
      id: "disp-q1",
      category: "HAZMAT Emergency",
      shortTitle: "Chlorine Gas Leak",
      prompt: "10-33 emergency call received: Chlorine chemical leak reported near sector 4 perimeter.",
    },
    {
      id: "disp-q2",
      category: "Motor Vehicle Collision",
      shortTitle: "10-50 on Route 9",
      prompt: "Unit 4 reporting a 10-50 personal injury collision on Route 9, requesting secondary EMS unit status.",
    },
    {
      id: "disp-q3",
      category: "Officer Distress",
      shortTitle: "Signal 13 Code Red",
      prompt: "Officer down on scene at 5th and Main, Signal 13, need immediate tactical backup and supervisor escalation.",
    },
    {
      id: "disp-q4",
      category: "Pursuit Policy",
      shortTitle: "PIT Maneuver Authorization",
      prompt: "What is our pursuit authorization and PIT maneuver policy for a fleeing stolen vehicle in heavy traffic?",
    },
    {
      id: "disp-q5",
      category: "Tactical Response",
      shortTitle: "Rescue Task Force Warm Zone",
      prompt: "Active violent threat reported at city transit center, initiating Rescue Task Force warm zone protocol.",
    },
    {
      id: "disp-q6",
      category: "HAZMAT Perimeter",
      shortTitle: "Evacuation Distances & Chemtrec",
      prompt: "Unit 12 on scene at track 4: toxic vapor cloud visible. Confirm downwind evacuation perimeter and Chemtrec alert.",
    },
    {
      id: "disp-q7",
      category: "Inter-Agency Mutual Aid",
      shortTitle: "Statewide Radio Patch",
      prompt: "Multi-agency mutual aid requested for 3-alarm structure fire, switch channel to Statewide TAC-2.",
    },
    {
      id: "disp-q8",
      category: "Priority Matrix",
      shortTitle: "Code 3 Authorization Check",
      prompt: "Can we authorize Code 3 emergency lights and sirens for a delayed cold property trespass report?",
    },
  ],

  healthcare: [
    {
      id: "health-q1",
      category: "Cardiac Emergency",
      shortTitle: "Crushing Chest Pain",
      prompt: "Patient is an adult male presenting with acute chest tightness radiating to the left arm and cold sweats.",
    },
    {
      id: "health-q2",
      category: "Stroke FAST",
      shortTitle: "FAST Screening & Window",
      prompt: "Caller has sudden right-sided facial drooping and slurred speech starting 45 minutes ago. What is our FAST protocol?",
    },
    {
      id: "health-q3",
      category: "Anaphylaxis",
      shortTitle: "Epinephrine IM Dosage",
      prompt: "Child experiencing severe peanut exposure with audible stridor and swollen lips. What is the emergency epinephrine IM dosage?",
    },
    {
      id: "health-q4",
      category: "Cardiac Contraindication",
      shortTitle: "Nitroglycerin & PDE-5",
      prompt: "Patient has chest pain but took sildenafil 12 hours ago. Can we administer sublingual nitroglycerin?",
    },
    {
      id: "health-q5",
      category: "Clinical Triage",
      shortTitle: "ESI Level Assignment",
      prompt: "Patient triage evaluation: vital signs stable, needs a routine stitch removal. What is the correct ESI Level?",
    },
    {
      id: "health-q6",
      category: "HIPAA & Privacy",
      shortTitle: "Minimum Necessary Rule",
      prompt: "A family member is demanding complete medical records over the phone. What are our HIPAA minimum necessary rules?",
    },
    {
      id: "health-q7",
      category: "Insurance & Billing",
      shortTitle: "Prior Authorization Protocol",
      prompt: "Specialist appointment requested for high-cost cardiac MRI. Do we need prior authorization on this PPO plan?",
    },
    {
      id: "health-q8",
      category: "Acute Deterioration",
      shortTitle: "Desaturation & Lethargy",
      prompt: "Adult patient in waiting room suddenly became lethargic with SpO2 dropping to 88%. Immediate triage reclassification needed.",
    },
  ],

  field_worker: [
    {
      id: "field-q1",
      category: "LOTO Safety",
      shortTitle: "OSHA 1910.147 Zero Energy",
      prompt: "Verifying zero energy state and OSHA 1910.147 lockout on hydraulic compressor 3.",
    },
    {
      id: "field-q2",
      category: "Safety Guardrail",
      shortTitle: "Attempted LOTO Bypass",
      prompt: "We are in a rush on conveyor motor M-402, can we just bypass LOTO for two minutes while replacing the belt?",
    },
    {
      id: "field-q3",
      category: "Diesel Diagnostics",
      shortTitle: "SPN 100 FMI 1 Low Oil",
      prompt: "Caterpillar generator engine is throwing SPN 100 FMI 1. What does that error indicate and what is our immediate action?",
    },
    {
      id: "field-q4",
      category: "Confined Space",
      shortTitle: "4-Gas Atmospheric Limits",
      prompt: "Walk me through the 4-gas atmospheric testing thresholds required before entering this underground vault.",
    },
    {
      id: "field-q5",
      category: "Electrical Safety",
      shortTitle: "NFPA 70E Arc Flash Boundary",
      prompt: "What are the NFPA 70E approach boundaries and required PPE category for opening a 480V motor control center?",
    },
    {
      id: "field-q6",
      category: "HVAC Diagnostics",
      shortTitle: "Superheat & Subcooling",
      prompt: "Commercial HVAC chiller has high superheat and high subcooling. What does this diagnosis point to?",
    },
    {
      id: "field-q7",
      category: "VFD Motor Controls",
      shortTitle: "Fault F005 OverVoltage",
      prompt: "PowerFlex VFD drive tripped on Fault F005 OverVoltage during deceleration. How do we test and clear this safely?",
    },
    {
      id: "field-q8",
      category: "Engine Overheat",
      shortTitle: "SPN 110 High Coolant Temp",
      prompt: "Diesel engine temperature is over 225 degrees Fahrenheit with SPN 110 FMI 0. Can I pop the radiator cap to check coolant?",
    },
  ],

  customer_support: [
    {
      id: "supp-q1",
      category: "Incident Escalation",
      shortTitle: "P0 Service Outage SLA",
      prompt: "Production API cluster is throwing 500 errors and our P0 enterprise SLA is breached.",
    },
    {
      id: "supp-q2",
      category: "Billing Operations",
      shortTitle: "$350 Duplicate Renewal Refund",
      prompt: "Customer was charged twice on an accidental annual renewal of $350. Am I authorized to issue an immediate refund?",
    },
    {
      id: "supp-q3",
      category: "API Developer Support",
      shortTitle: "HTTP 429 Jitter Backoff",
      prompt: "Our developer REST API calls are failing with HTTP 429 Too Many Requests. How do we implement proper jitter backoff?",
    },
    {
      id: "supp-q4",
      category: "Identity & SSO",
      shortTitle: "Invalid SAML Signature",
      prompt: "Enterprise client is experiencing an 'Invalid SAML Response signature' error on Okta SSO login.",
    },
    {
      id: "supp-q5",
      category: "Account Security",
      shortTitle: "MFA Telephone Bypass Request",
      prompt: "Customer calling from an unknown phone number demands an immediate phone reset of their MFA authenticator.",
    },
    {
      id: "supp-q6",
      category: "VIP Retention",
      shortTitle: "Enterprise Churn Mitigation",
      prompt: "VIP enterprise account with $40k contract wants to cancel due to budget cuts. What concessions can I offer?",
    },
    {
      id: "supp-q7",
      category: "Chargeback Disputes",
      shortTitle: "Reason Code 10.4 Pack",
      prompt: "We received a credit card chargeback with reason code 10.4 fraud. What documents must we submit within 7 days?",
    },
    {
      id: "supp-q8",
      category: "SCIM Provisioning",
      shortTitle: "SCIM 401 Bearer Token Expiry",
      prompt: "Our SCIM user provisioning in Azure AD returned 401 Unauthorized. What is the token expiration lifecycle?",
    },
  ],

  logistics_fleet: [
    {
      id: "log-q1",
      category: "Cold Chain",
      shortTitle: "Reefer Exceeds 42°F",
      prompt: "Refrigerated trailer reefer temperature exceeded 42 degrees Fahrenheit on interstate transit. What is the FSMA protocol?",
    },
    {
      id: "log-q2",
      category: "FMCSA Compliance",
      shortTitle: "11-Hour Driving Rule",
      prompt: "Driver has completed 11 hours of driving but is 30 miles from home. Can they keep driving under the 14-hour rule?",
    },
    {
      id: "log-q3",
      category: "Aviation Dispatch",
      shortTitle: "Part 121 Alternate Fuel",
      prompt: "Part 121 domestic flight dispatch: ceiling is forecast at 1,500 feet at destination. Do we need an alternate airport?",
    },
    {
      id: "log-q4",
      category: "CVSA Roadside",
      shortTitle: "Steer Tire 3/32 Tread Depth",
      prompt: "Roadside CVSA inspection found steer axle tire tread depth at 3/32 inch. Does this trigger an out-of-service order?",
    },
    {
      id: "log-q5",
      category: "Cold Chain Pharma",
      shortTitle: "Frozen Cargo Temperature Limits",
      prompt: "Frozen pharma shipment trailer dropped to -5°F. What are the allowable temperature limits for frozen cargo?",
    },
    {
      id: "log-q6",
      category: "Fleet Compliance",
      shortTitle: "ELD Malfunction Paper Log",
      prompt: "Driver ELD device malfunctioned on route. What is the mandatory reporting window and paper log procedure?",
    },
    {
      id: "log-q7",
      category: "Aviation Maintenance",
      shortTitle: "MEL Category B Rectification",
      prompt: "What is the Category B rectification interval for an inoperative avionics item under the Minimum Equipment List?",
    },
    {
      id: "log-q8",
      category: "Cargo Securement",
      shortTitle: "Working Load Limit 50%",
      prompt: "Flatbed tiedowns are rated for 15,000 lbs on a 40,000 lb steel coil. Does this meet CVSA cargo securement rules?",
    },
  ],

  financial_compliance: [
    {
      id: "fin-q1",
      category: "AML Monitoring",
      shortTitle: "Structuring Detection $9,800",
      prompt: "Multiple structured wire transfers of $9,800 detected within 24 hours under the same beneficiary.",
    },
    {
      id: "fin-q2",
      category: "BSA CTR Filing",
      shortTitle: "$10,500 Cash Across Tellers",
      prompt: "Customer deposited $10,500 in physical currency across two teller windows today. Is a CTR Form 112 required?",
    },
    {
      id: "fin-q3",
      category: "Anti-Structuring",
      shortTitle: "Split $15k Deposits Inquiry",
      prompt: "Can a customer deposit $15,000 in cash without a CTR if they split it into three $5,000 deposits across three days?",
    },
    {
      id: "fin-q4",
      category: "Regulation E",
      shortTitle: "Consumer Liability 2-Day Tier",
      prompt: "Customer reports unauthorized debit card transactions 5 days after their wallet was stolen. What is their Regulation E liability?",
    },
    {
      id: "fin-q5",
      category: "Fraud Emergency",
      shortTitle: "Simultaneous Logins NY & Tokyo",
      prompt: "Simultaneous logins from New York and Tokyo detected on commercial account. What is the emergency freeze protocol?",
    },
    {
      id: "fin-q6",
      category: "Wire Operations",
      shortTitle: "Dual-Control & OFAC SDN Match",
      prompt: "Outbound international wire of $85,000 to an unverified overseas supplier. Does this require dual authorization and OFAC screening?",
    },
    {
      id: "fin-q7",
      category: "BSA Whistleblower",
      shortTitle: "SAR Tipping Off Prohibition",
      prompt: "Customer claims bank tipping off rules don't apply to them and demands to know if a SAR was filed. Can we disclose?",
    },
    {
      id: "fin-q8",
      category: "Dispute Timeline",
      shortTitle: "Reg E 60-Day Liability Cutoff",
      prompt: "Debit card dispute reported 75 days after statement date. Does the bank still bear full liability under Reg E?",
    },
  ],
};

/**
 * Retrieves the questions for a specific vertical, with a safe fallback.
 */
export function getCallerQuestions(verticalId: string): CallerQuestion[] {
  return CALLER_QUESTIONS[verticalId] || CALLER_QUESTIONS.dispatch;
}

/**
 * Gets the next caller question for a vertical based on an offset or index,
 * guaranteeing a non-repeating cycle of unique questions.
 */
export function getNextCallerQuestion(
  verticalId: string,
  currentIndex: number
): { question: CallerQuestion; nextIndex: number } {
  const list = getCallerQuestions(verticalId);
  const safeIndex = (currentIndex >= 0 ? currentIndex : 0) % list.length;
  const question = list[safeIndex];
  const nextIndex = (safeIndex + 1) % list.length;
  return { question, nextIndex };
}
