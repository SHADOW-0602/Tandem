<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class VerticalController extends Controller
{
    private static function getVerticalsData(): array
    {
        $knowledgeBasePath = base_path('../agent/knowledge');

        return [
            'dispatch' => [
                'id' => 'dispatch',
                'name' => '911 & Tactical CAD Dispatch',
                'description' => 'High-velocity dispatch assistant for field units, emergency APCO 10-codes, and HAZMAT ERG perimeter isolation.',
                'icon' => 'Radio',
                'moss_index' => 'dispatch_emergency_ops',
                'knowledge_file' => 'dispatch_sops.json',
                'sample_prompts' => [
                    'Unit 4 reporting a 10-50 on Route 9, request backup status',
                    'What is the initial isolation distance for a chlorine gas leak?',
                    'Officer down on scene, Signal 13, need immediate assistance',
                ],
                'latency_target_ms' => 590,
                'character' => [
                    'name' => 'Commander Vance',
                    'title' => 'Tactical CAD & Emergency Dispatch Lead',
                    'callsign' => 'VANCE-01',
                    'quote' => 'Hold your perimeter. Backup coordinates inbound.',
                ],
                'guardrails' => [
                    [
                        'id' => 'officer_down_immediate_priority',
                        'name' => 'Officer Down Code Red',
                        'description' => 'Signal 13 or officer down overrides queue to priority dispatch.',
                        'trigger_phrases' => ['officer down', 'signal 13', 'shots fired at unit', '10-99 officer in danger'],
                        'severity' => 'CRITICAL',
                        'action' => 'IMMEDIATE_DISPATCH_ALL_AVAILABLE_UNITS',
                        'override_message' => 'ATTENTION ALL UNITS: Signal 13 / Officer Down reported. Clearing all channels for priority emergency traffic. Medical and backup dispatched code 3.',
                    ]
                ],
            ],
            'healthcare' => [
                'id' => 'healthcare',
                'name' => 'Clinical & Emergency Triage',
                'description' => 'Hospital triage & clinical support covering ESI Levels 1-5, ACS cardiac protocols, Cincinnati Stroke FAST, and HIPAA.',
                'icon' => 'Stethoscope',
                'moss_index' => 'clinical_healthcare_triage',
                'knowledge_file' => 'healthcare_triage.json',
                'sample_prompts' => [
                    'Patient has crushing substernal chest pain and shortness of breath',
                    'What are the FAST stroke screening steps and therapeutic window?',
                    'What is the adult intramuscular dose for epinephrine in anaphylaxis?',
                ],
                'latency_target_ms' => 590,
                'character' => [
                    'name' => 'Dr. Maya Lin',
                    'title' => 'Chief Clinical Triage Specialist',
                    'callsign' => 'MED-TRIAGE',
                    'quote' => 'Airway, breathing, circulation first. Let\'s stabilize right now.',
                ],
                'guardrails' => [
                    [
                        'id' => 'chest_pain_emergency_triage',
                        'name' => 'Acute Coronary Syndrome Escalation',
                        'description' => 'Crushing chest pain requires immediate ESI-2 code team.',
                        'trigger_phrases' => ['crushing chest pain', 'chest pressure radiating to jaw', 'chest pain and shortness of breath', 'suspected myocardial infarction'],
                        'severity' => 'EMERGENCY',
                        'action' => 'ACTIVATE_CODE_STEMI_PROTOCOL',
                        'override_message' => 'CRITICAL TRIAGE ALERT: Immediate ESI Level 2 protocol activated. Directing patient to Resuscitation Bay 1. Notifying interventional cardiology team immediately.',
                    ]
                ],
            ],
            'field_worker' => [
                'id' => 'field_worker',
                'name' => 'Field Ops & Industrial Safety',
                'description' => 'OSHA 1910.147 Lockout/Tagout (LOTO), heavy diesel SPN/FMI engine diagnostics, HVAC superheat, and NFPA 70E.',
                'icon' => 'HardHat',
                'moss_index' => 'enterprise_field_and_support',
                'knowledge_file' => 'field_worker_loto.json',
                'sample_prompts' => [
                    'Walk me through the 6 steps of OSHA Lockout Tagout zero energy verification',
                    'Caterpillar engine is throwing SPN 100 FMI 1, what does that mean?',
                    'What are the 4-gas atmospheric limits for confined space entry?',
                ],
                'latency_target_ms' => 590,
                'character' => [
                    'name' => 'Axel Miller',
                    'title' => 'Lead Industrial Safety Foreman',
                    'callsign' => 'OSHA-RIG',
                    'quote' => 'Verify zero energy state before you touch a single breaker.',
                ],
                'guardrails' => [
                    [
                        'id' => 'loto_zero_energy_violation',
                        'name' => 'Zero Energy Verification Failure',
                        'description' => 'Working on energized equipment without isolation triggers stop-work.',
                        'trigger_phrases' => ['skip zero energy test', 'bypass lockout', 'leave breaker on while servicing', 'working hot without permit'],
                        'severity' => 'STOP_WORK',
                        'action' => 'TRIGGER_MANDATORY_STOP_WORK_ORDER',
                        'override_message' => 'STOP WORK IMMEDIATELY: OSHA 1910.147 violation detected. All servicing must cease until zero energy state is verified by test meter. Safety lead notified.',
                    ]
                ],
            ],
            'customer_support' => [
                'id' => 'customer_support',
                'name' => 'Enterprise Support & SLA',
                'description' => 'Enterprise Tier-1 support, 15-minute P0 response SLA, automated $500 refund threshold, and HTTP 429 API backoff.',
                'icon' => 'Headphones',
                'moss_index' => 'enterprise_field_and_support',
                'knowledge_file' => 'customer_support_sla.json',
                'sample_prompts' => [
                    'What is our response SLA for a P0 critical system outage?',
                    'Can I issue an immediate $350 refund for an accidental renewal?',
                    'Customer is getting HTTP 429 errors on the REST API, how to troubleshoot?',
                ],
                'latency_target_ms' => 590,
                'character' => [
                    'name' => 'Elena Frost',
                    'title' => 'Executive SLA & Escalations Concierge',
                    'callsign' => 'SLA-CORE',
                    'quote' => 'Consider your issue prioritized. I\'m handling the fix directly.',
                ],
                'guardrails' => [
                    [
                        'id' => 'unauthorized_large_refund',
                        'name' => 'Refund Threshold Exceeded',
                        'description' => 'Refunds exceeding $500 require director approval.',
                        'trigger_phrases' => ['refund over $500', 'issue $1000 credit without approval', 'refund entire annual enterprise contract'],
                        'severity' => 'COMPLIANCE_HOLD',
                        'action' => 'ROUTE_TO_FINANCE_DIRECTOR_APPROVAL',
                        'override_message' => 'COMPLIANCE NOTICE: Auto-refund limit is capped at $500 per incident under SOC2 policy. This request has been escalated to the Finance Director for expedited sign-off.',
                    ]
                ],
            ],
            'logistics_fleet' => [
                'id' => 'logistics_fleet',
                'name' => 'Fleet Logistics & Aviation',
                'description' => 'FMCSA Hours of Service compliance, FDA FSMA cold-chain temperature monitoring, and Part 121 aviation dispatch.',
                'icon' => 'Truck',
                'moss_index' => 'dispatch_emergency_ops',
                'knowledge_file' => 'logistics_fleet.json',
                'sample_prompts' => [
                    'What is the FMCSA 11-hour driving rule and 14-hour on-duty window?',
                    'Reefer temperature just exceeded 42 degrees, what is the protocol?',
                    'What is the alternate airport fuel reserve requirement under Part 121?',
                ],
                'latency_target_ms' => 590,
                'character' => [
                    'name' => 'Captain Sarah Cross',
                    'title' => 'Global Logistics & Aviation Controller',
                    'callsign' => 'NAV-AIR',
                    'quote' => 'Clear skies or rough turbulence, cargo stays protected.',
                ],
                'guardrails' => [],
            ],
            'financial_compliance' => [
                'id' => 'financial_compliance',
                'name' => 'Banking Compliance & Fraud',
                'description' => 'Bank Secrecy Act AML reporting, Currency Transaction Reports, Regulation E disputes, and emergency card freeze.',
                'icon' => 'ShieldCheck',
                'moss_index' => 'enterprise_field_and_support',
                'knowledge_file' => 'financial_compliance.json',
                'sample_prompts' => [
                    'When is a Currency Transaction Report mandatory under BSA?',
                    'What are the consumer liability tiers for unauthorized transfers under Reg E?',
                    'Customer reports unauthorized debit transactions, what is the emergency freeze protocol?',
                ],
                'latency_target_ms' => 590,
                'character' => [
                    'name' => 'Marcus Sterling',
                    'title' => 'Principal Fraud & AML Special Agent',
                    'callsign' => 'BSA-AUDIT',
                    'quote' => 'Flag the suspicious pattern and enforce immediate account shielding.',
                ],
                'guardrails' => [],
            ],
        ];
    }

    public function index()
    {
        $verticals = array_values(self::getVerticalsData());
        return response()->json($verticals);
    }

    public function show(string $id)
    {
        $all = self::getVerticalsData();
        if (!isset($all[$id])) {
            return response()->json(['message' => "Vertical '$id' not found"], 404);
        }
        return response()->json($all[$id]);
    }
}
