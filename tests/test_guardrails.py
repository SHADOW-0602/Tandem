from agent.guardrails import evaluate_guardrails

def test_dispatch_guardrails():
    # Signal 13 / officer down should trigger critical escalation
    res = evaluate_guardrails("dispatch", "Unit 2, we have an officer down on scene, Signal 13!")
    assert res is not None
    action, severity, msg = res
    assert severity == "CRITICAL"
    assert "SUPERVISOR" in action
    assert "Signal 13" in msg

    # Normal communication should not trigger
    res_normal = evaluate_guardrails("dispatch", "Unit 4 arrived at location, 10-8")
    assert res_normal is None

def test_healthcare_guardrails():
    # Severe chest pain should trigger emergency 911 dispatch
    res = evaluate_guardrails("healthcare", "Patient has crushing chest pain and left arm numbness")
    assert res is not None
    action, severity, msg = res
    assert severity == "CRITICAL"
    assert "EMERGENCY_911" in action
    assert "911" in msg

    # Diagnosis demand should trigger clinical disclaimer
    res_diag = evaluate_guardrails("healthcare", "Can you diagnose me and tell me what illness I have?")
    assert res_diag is not None
    action, severity, msg = res_diag
    assert severity == "MEDIUM"
    assert "DISCLAIMER" in action

def test_field_worker_guardrails():
    # Gas leak / explosive vapor should trigger immediate evacuation
    res = evaluate_guardrails("field_worker", "We smell a heavy gas leak near the turbine")
    assert res is not None
    action, severity, msg = res
    assert severity == "CRITICAL"
    assert "EVACUATION" in action

def test_customer_support_guardrails():
    # Legal threat triggers supervisor
    res = evaluate_guardrails("customer_support", "I am going to hire a lawyer and sue your company")
    assert res is not None
    action, severity, msg = res
    assert severity == "HIGH"
    assert "LEGAL" in action
