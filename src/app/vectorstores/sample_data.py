"""
Balanced musculoskeletal sample dataset
"""

SAMPLE_DOCUMENTS = [

    # ------------------------
    # 3 NECK CONDITIONS
    # ------------------------

    {
        "title": "Text Neck Syndrome",
        "content": """
Neck strain from prolonged phone or laptop use.

Indicators:
- Pain after screen use
- Forward head posture
- Upper back tightness

Treatment:
Posture correction and mobility work.

Exercises:
Chin tucks, thoracic extension.

Recovery:
3–8 weeks.
""",
        "tags": ["neck", "posture", "technology"]
    },

    {
        "title": "Whiplash Injury",
        "content": """
Acceleration-deceleration neck trauma.

Indicators:
- Neck stiffness
- Headache
- Limited motion after accident

Treatment:
Gradual mobility, physical therapy.

Exercises:
ROM drills, light isometrics.

Recovery:
2–8 weeks.
""",
        "tags": ["neck", "trauma", "whiplash"]
    },

    {
        "title": "Neck Muscle Strain",
        "content": """
Overstretch or overload of neck muscles.

Indicators:
- Local soreness
- Pain with movement
- No arm radiation

Treatment:
Rest, heat, manual therapy.

Exercises:
Gentle stretching and strengthening.

Recovery:
1–4 weeks.
""",
        "tags": ["neck", "muscle", "strain"]
    },


    # ------------------------
    # 3 CERVICAL CONDITIONS
    # ------------------------

    {
        "title": "Cervical Radiculopathy",
        "content": """
Compression of cervical nerve root.

Indicators:
- Arm numbness
- Radiating pain
- Tingling in hand

Treatment:
Physical therapy, posture correction.

Exercises:
Nerve glides, chin tucks.

Recovery:
3–10 weeks.
""",
        "tags": ["cervical", "nerve", "radiating pain"]
    },

    {
        "title": "Cervical Disc Herniation",
        "content": """
Disc bulge pressing on cervical nerves.

Indicators:
- Severe neck pain
- Arm weakness
- Symptoms worse with coughing

Treatment:
Medical evaluation, PT.

Exercises:
Extension drills, deep neck flexor work.

Recovery:
6–12 weeks.
""",
        "tags": ["cervical", "disc", "herniation"]
    },

    {
        "title": "Cervical Spondylosis",
        "content": """
Degenerative arthritis of cervical spine.

Indicators:
- Chronic stiffness
- Reduced mobility
- Age-related pain

Treatment:
Mobility and strengthening program.

Exercises:
Neck stabilization drills.

Recovery:
Chronic condition, symptom-managed.
""",
        "tags": ["cervical", "degeneration", "arthritis"]
    },


    # ------------------------
    # 2 SHOULDER CONDITIONS
    # ------------------------

    {
        "title": "Shoulder Impingement Syndrome",
        "content": """
Compression of rotator cuff under acromion.

Indicators:
- Pain lifting arm overhead
- Weakness
- Night discomfort

Treatment:
Load management, PT.

Exercises:
Rotator cuff strengthening, scapular control.

Recovery:
4–10 weeks.
""",
        "tags": ["shoulder", "impingement", "rotator cuff"]
    },

    {
        "title": "Rotator Cuff Tear",
        "content": """
Partial or full tear of shoulder tendons.

Indicators:
- Weak lifting
- Pain with rotation
- Limited overhead motion

Treatment:
PT or surgery (severe cases).

Exercises:
Strengthening after inflammation reduces.

Recovery:
8–16 weeks (non-surgical).
""",
        "tags": ["shoulder", "rotator cuff", "tear"]
    },


    # ------------------------
    # 2 KNEE LIGAMENT INJURIES
    # ------------------------

    {
        "title": "ACL Tear",
        "content": """
Anterior cruciate ligament injury in knee.

Indicators:
- Popping sound
- Knee instability
- Swelling after pivoting

Treatment:
Surgery for athletes, rehab required.

Exercises:
Quadriceps strengthening, balance training.

Recovery:
6–9 months post-surgery.
""",
        "tags": ["knee", "acl", "ligament"]
    },

    {
        "title": "PCL Tear",
        "content": """
Posterior cruciate ligament injury.

Indicators:
- Knee pain after fall on bent knee
- Instability descending stairs
- Mild swelling

Treatment:
Bracing and rehabilitation.

Exercises:
Hamstring control, quad strengthening.

Recovery:
3–6 months.
""",
        "tags": ["knee", "pcl", "ligament"]
    }

]


def get_sample_documents():
    return SAMPLE_DOCUMENTS


def get_documents_by_tag(tag: str):
    return [doc for doc in SAMPLE_DOCUMENTS if tag in doc.get("tags", [])]