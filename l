import json

with open('curriculum.json', 'r') as f:
    data = json.load(f)

meta = data.get('meta', {})
curriculum = data.get('curriculum', [])

print(f"=== CURRICULUM AUDIT REPORT ===")
print(f"Meta Total Topics Target: {meta.get('total_topics')}")

total_courses = len(curriculum)
total_units = 0
total_topics = 0

for course in curriculum:
    c_id = course.get('course_id')
    c_name = course.get('course_name')
    units = course.get('units', [])
    total_units += len(units)
    course_topics = sum(len(u.get('topics', [])) for u in units)
    total_topics += course_topics
    print(f"Course: {c_id} - {c_name} | Units: {len(units)} | Topics: {course_topics}")

print("--------------------------------")
print(f"Total Courses: {total_courses}")
print(f"Total Units:   {total_units}")
print(f"Total Topics:  {total_topics}")
