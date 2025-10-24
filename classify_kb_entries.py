"""
Classify all 11,215 KB entries by profession and cv_section
Run: python manage.py shell < classify_kb_entries.py
"""

import logging
from django.db.models import Count
from cv_gen.models import KnowledgeBase

logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("CLASSIFYING ALL KB ENTRIES BY PROFESSION & SECTION")
print("="*80)

# Keywords for profession detection
PROFESSION_KEYWORDS = {
    'Accountant': ['account', 'accounting', 'ledger', 'reconcil', 'payable', 'receivable', 'financial', 'gafs', 'deams'],
    'Backend Developer': ['backend', 'api', 'server', 'database', 'python', 'java', 'nodejs', 'microservice'],
    'Frontend Developer': ['frontend', 'ui', 'ux', 'react', 'angular', 'vue', 'html', 'css', 'javascript'],
    'Manager': ['manager', 'lead', 'supervise', 'team', 'direct', 'manage', 'leadership', 'supervisor'],
    'DevOps Engineer': ['devops', 'docker', 'kubernetes', 'deployment', 'ci/cd', 'infrastructure', 'aws', 'cloud'],
    'Data Scientist': ['data', 'machine learning', 'analytics', 'python', 'sql', 'analysis'],
    'QA Engineer': ['testing', 'test', 'qa', 'quality', 'automation'],
}

# Keywords for section detection
SECTION_KEYWORDS = {
    'summary': ['specialized', 'expertise', 'background', 'professional', 'summary', 'experience in'],
    'achievement': ['managed', 'led', 'implemented', 'developed', 'improved', 'achieved', 'increased', 'reduced', 'optimized'],
    'experience': ['responsible', 'duties', 'role', 'position', 'worked', 'assigned'],
    'skill': ['proficient', 'knowledge', 'expertise', 'experience with', 'skilled'],
}

# Process all KB entries
entries = KnowledgeBase.objects.all()
total = entries.count()
processed = 0
errors = 0

print(f"\nProcessing {total} KB entries...\n")

for i, entry in enumerate(entries, 1):
    try:
        # Detect profession
        content_lower = (entry.content.lower() + entry.title.lower())[:1000]
        detected_profession = 'General'
        
        for profession, keywords in PROFESSION_KEYWORDS.items():
            if any(kw in content_lower for kw in keywords):
                detected_profession = profession
                break
        
        # Detect section
        detected_section = 'achievement'
        for section, keywords in SECTION_KEYWORDS.items():
            if any(kw in content_lower for kw in keywords):
                detected_section = section
                break
        
        # Detect content type
        word_count = len(entry.content.split())
        if word_count > 300:
            detected_type = 'job_description'
        elif word_count > 100:
            detected_type = 'paragraph'
        else:
            detected_type = 'bullet'
        
        # Update entry
        entry.profession = detected_profession
        entry.cv_section = detected_section
        entry.content_type = detected_type
        entry.word_count = word_count
        entry.save(update_fields=['profession', 'cv_section', 'content_type', 'word_count'])
        
        processed += 1
        if i % 500 == 0:
            pct = (i * 100) // total
            print(f"  Progress: {i}/{total} ({pct}%)")
        
    except Exception as e:
        errors += 1
        logger.error(f"Error processing entry {entry.id}: {e}")
        continue

print(f"\n✅ Classification complete!")
print(f"  ├─ Total processed: {processed}")
print(f"  ├─ Errors: {errors}")
print(f"  └─ Success rate: {((processed-errors)*100)//processed}%")

# Show statistics
print(f"\n📊 Statistics:")
print(f"\nBy Profession:")
stats = KnowledgeBase.objects.values('profession').annotate(count=Count('id')).order_by('-count')
for stat in stats:
    print(f"  ├─ {stat['profession']}: {stat['count']} entries")

print(f"\nBy CV Section:")
stats = KnowledgeBase.objects.values('cv_section').annotate(count=Count('id')).order_by('-count')
for stat in stats:
    print(f"  ├─ {stat['cv_section']}: {stat['count']} entries")

print(f"\nBy Content Type:")
stats = KnowledgeBase.objects.values('content_type').annotate(count=Count('id')).order_by('-count')
for stat in stats:
    print(f"  ├─ {stat['content_type']}: {stat['count']} entries")

print("\n" + "="*80)
print("✅ KB CLASSIFICATION COMPLETE!")
print("="*80 + "\n")