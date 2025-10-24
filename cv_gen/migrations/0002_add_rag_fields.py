"""
Migration to add RAG enhancement fields to KnowledgeBase
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cv_gen', '0001_initial'),
    ]

    operations = [
        # Add new fields to KnowledgeBase
        migrations.AddField(
            model_name='knowledgebase',
            name='profession',
            field=models.CharField(
                choices=[
                    ('Accountant', 'Accountant'),
                    ('Accounts Payable Specialist', 'Accounts Payable Specialist'),
                    ('Financial Analyst', 'Financial Analyst'),
                    ('Backend Developer', 'Backend Developer'),
                    ('Frontend Developer', 'Frontend Developer'),
                    ('Full Stack Developer', 'Full Stack Developer'),
                    ('DevOps Engineer', 'DevOps Engineer'),
                    ('Data Scientist', 'Data Scientist'),
                    ('Manager', 'Manager'),
                    ('General', 'General'),
                ],
                default='General',
                max_length=100,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='cv_section',
            field=models.CharField(
                choices=[
                    ('summary', 'Professional Summary'),
                    ('experience', 'Experience Description'),
                    ('achievement', 'Achievement Bullet'),
                    ('skill', 'Skill'),
                    ('education', 'Education'),
                    ('certification', 'Certification'),
                ],
                default='achievement',
                max_length=50,
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='content_type',
            field=models.CharField(
                choices=[
                    ('bullet', 'Single Bullet Point'),
                    ('paragraph', 'Full Paragraph'),
                    ('job_description', 'Complete Job Description'),
                ],
                default='bullet',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='confidence_score',
            field=models.FloatField(default=1.0),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='word_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='knowledgebase',
            name='source_document',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='cvdocument',
            name='profession',
            field=models.CharField(
                choices=[
                    ('Accountant', 'Accountant'),
                    ('Backend Developer', 'Backend Developer'),
                    ('Frontend Developer', 'Frontend Developer'),
                    ('Manager', 'Manager'),
                    ('General', 'General'),
                ],
                db_index=True,
                default='General',
                max_length=100,
            ),
        ),
        
        # Create new models
        migrations.CreateModel(
            name='CVGenerationFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_type', models.CharField(max_length=50, choices=[
                    ('summary', 'Professional Summary'),
                    ('experience', 'Experience Description'),
                    ('achievement', 'Achievement Bullet'),
                ])),
                ('generated_content', models.TextField()),
                ('rating', models.IntegerField(choices=[(1, '⭐ Poor'), (2, '⭐⭐ Fair'), (3, '⭐⭐⭐ Good'), (4, '⭐⭐⭐⭐ Very Good'), (5, '⭐⭐⭐⭐⭐ Excellent')])),
                ('feedback_text', models.TextField(blank=True)),
                ('was_helpful', models.BooleanField(default=True)),
                ('suggested_improvement', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cv_document', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='feedback', to='cv_gen.cvdocument')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        
        migrations.CreateModel(
            name='RAGCache',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profession', models.CharField(db_index=True, max_length=100)),
                ('cv_section', models.CharField(db_index=True, max_length=50)),
                ('query_hash', models.CharField(db_index=True, max_length=64, unique=True)),
                ('query_text', models.TextField()),
                ('cached_results', models.JSONField()),
                ('hit_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('accessed_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        
        # Add database indexes
        migrations.AddIndex(
            model_name='knowledgebase',
            index=models.Index(fields=['profession', 'cv_section'], name='cv_gen_know_profes_cv_sec_idx'),
        ),
        migrations.AddIndex(
            model_name='knowledgebase',
            index=models.Index(fields=['profession', 'category'], name='cv_gen_know_profes_categ_idx'),
        ),
    ]