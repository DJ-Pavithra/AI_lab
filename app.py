from flask import Flask, render_template, request, url_for, redirect, flash
from pyswip import Prolog
import os
import matplotlib
matplotlib.use('Agg')  # headless-safe
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from flask import render_template_string

app = Flask(__name__)
app.secret_key = "dev-secret" 

# Ensure static dir exists
os.makedirs("static", exist_ok=True)

def new_prolog():
    p = Prolog()
    p.consult("learningpath.pl")
    return p

def reset_and_assert(p: Prolog, goal: str, skills: list, time_hours: int, user_level: str = "beginner", learning_style: str = "practical"):
    list(p.query("reset_user_facts."))
    p.assertz(f"student_goal({goal})")
    p.assertz(f"time_available({time_hours})")
    p.assertz(f"user_level({user_level})")
    p.assertz(f"learning_style({learning_style})")
    for s in skills:
        s = s.strip()
        if s:
            p.assertz(f"known({s})")

def prolog_list(query_str, var):
    """Run query that returns list values one-by-one, collect `var`."""
    p = new_prolog()
    res = [r[var] for r in p.query(query_str)]
    return [str(v) for v in res]

def get_topic_info(p: Prolog, topic_atom: str) -> dict:
    """Get comprehensive topic information including duration, difficulty, category, and description."""
    try:
        result = list(p.query(f"topic({topic_atom}, _, D, Diff, Cat, Desc)"))
        if result:
            return {
                'duration': int(result[0]['D']),
                'difficulty': str(result[0]['Diff']),
                'category': str(result[0]['Cat']),
                'description': str(result[0]['Desc'])
            }
        return {'duration': 0, 'difficulty': 'unknown', 'category': 'unknown', 'description': 'No description available'}
    except Exception:
        return {'duration': 0, 'difficulty': 'unknown', 'category': 'unknown', 'description': 'Error retrieving information'}

@app.route("/", methods=["GET"])
def home():
    p = new_prolog()
    goals = [str(r['Goal']) for r in p.query("goal_topics(Goal, _)")]
    return render_template("index.html", goals=goals)

@app.route("/recommend", methods=["POST"])
def recommend():
    goal = request.form.get("goal", "").strip()
    skills_raw = request.form.get("skills", "")
    time_str = request.form.get("time", "0").strip()
    user_level = request.form.get("user_level", "beginner")
    learning_style = request.form.get("learning_style", "practical")

    # Clean inputs
    skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
    try:
        time_hours = int(time_str)
    except ValueError:
        flash("Please enter a valid number for available time (hours).", "error")
        return redirect(url_for("home"))

    p = new_prolog()
    reset_and_assert(p, goal, skills, time_hours, user_level, learning_style)

    # Build ordered path (topics)
    try:
        q = list(p.query(f"path_to_goal({goal}, Path)"))
        if not q:
            flash("No eligible topics found for the given input.", "warning")
            return redirect(url_for("home"))

        ordered_topics = q[0]['Path']  # list of atoms
    except Exception as e:
        print(f"Error building path: {e}")
        flash("Error building learning path. Please try again.", "error")
        return redirect(url_for("home"))
    
    # Enhanced path with comprehensive information
    path_data = []
    total_time = 0
    for t in ordered_topics:
        t_str = str(t)
        info = get_topic_info(p, t_str)
        # Check progress state using new Prolog predicate
        try:
            is_complete = bool(list(p.query(f'is_topic_complete({t_str})')))
        except Exception:
            is_complete = False
        path_data.append({
            'topic': t_str,
            'duration': info['duration'],
            'difficulty': info['difficulty'],
            'category': info['category'],
            'description': info['description'],
            'complete': is_complete
        })
        total_time += info['duration']

    # Enhanced suggestion with arithmetic
    suggestion = ""
    try:
        suggest_q = list(p.query(f"study_suggestion({total_time}, {time_hours}, Suggestion)"))
        suggestion = str(suggest_q[0]['Suggestion']) if suggest_q else ""
    except Exception as e:
        print(f"Error getting suggestion: {e}")
        suggestion = "Time analysis completed successfully."

    # ---- Comprehensive Prolog Concepts Showcase ----

    # 1. UNIFICATION: Same-duration topic pairs
    same_dur_pairs = []
    seen_pairs = set()
    try:
        for r in p.query(f"goal_path_same_duration_topics({goal}, T1, T2)"):
            t1, t2 = str(r['T1']), str(r['T2'])
            key = tuple(sorted((t1, t2)))
            if key not in seen_pairs:
                seen_pairs.add(key)
                same_dur_pairs.append(key)
                if len(same_dur_pairs) >= 15:
                    break
    except Exception as e:
        print(f"Error getting same duration topics: {e}")
        same_dur_pairs = []

    # Update in the recommend() function where same_diff_pairs is handled

    # 2. UNIFICATION: Same-difficulty topics
    same_diff_pairs = []
    seen_diff_pairs = set()
    try:
        for r in p.query("same_difficulty_topics(T1, T2)"):
            t1, t2 = str(r['T1']), str(r['T2'])
            key = tuple(sorted((t1, t2)))
            if key not in seen_diff_pairs:
                seen_diff_pairs.add(key)
                same_diff_pairs.append((t1, t2))
            if len(same_diff_pairs) >= 10:
                break
    except Exception as e:
        print(f"Error getting same difficulty topics: {e}")
        same_diff_pairs = []

    # 5. CUT OPERATION: Only the first learnable topic
    first_topic = None
    try:
        cut_q = list(p.query("first_learnable_topic(T)"))
        if cut_q:
            first_topic = str(cut_q[0]['T'])
    except Exception as e:
        print(f"Error getting first learnable topic: {e}")
        first_topic = None

    # 6. NEGATION: Topics you cannot learn yet
    cannot = []
    try:
            
        cannot = [str(r['Topic']) for r in p.query("cannot_learn(Topic)")]
    except Exception as e:
        print(f"Error getting cannot learn topics: {e}")
        cannot = []

    # 7. ARITHMETIC + LIST OPERATIONS: Short topics and list operations
    short_threshold = 8
    short_topics = []
    long_topics = []
    try:
        short_topics = [str(r['Topic']) for r in p.query(f"short_topics({short_threshold}, Topic)")]
        long_topics = [str(r['Topic']) for r in p.query(f"long_topics({short_threshold}, Topic)")]
    except Exception as e:
        print(f"Error getting short/long topics: {e}")
        short_topics = []
        long_topics = []
    
   # Modified intersection code
    intersection = []
    try:
        # Get goal topics
        goal_set = [str(x) for x in list(p.query(f"goal_topics({goal}, L)"))[0]['L']]
        # Get short topics
        short_topics = [str(r['Topic']) for r in p.query(f"short_topics({short_threshold}, Topic)")]
        
        # Use findall to get intersection
        intersection_query = (
            f"findall(X, ("
            f"member(X, {goal_set}), "
            f"member(X, {short_topics})), "
            f"Intersection)"
        )
        result = list(p.query(intersection_query))
        if result:
            intersection = [str(x) for x in result[0]['Intersection']]
    except Exception as e:
        print(f"Error getting list intersection: {e}")
        intersection = []
    # 8. QUANTIFIERS: Existential and Universal
    some_topic = None
    try:
        some_q = list(p.query("some_topic_available_to_learn(T)"))
        if some_q:
            some_topic = str(some_q[0]['T'])
    except Exception as e:
        print(f"Error getting some topic: {e}")
        some_topic = None

    # Universal: are all prereqs known for react?
    universal_demo_topic = "react"
    all_prereqs_known = False
    try:
        all_known_q = list(p.query(f"all_prerequisites_known({universal_demo_topic})"))
        all_prereqs_known = bool(all_known_q)
    except Exception as e:
        print(f"Error checking all prerequisites known: {e}")
        all_prereqs_known = False

    # 9. RECURSION: All prerequisites recursively
    all_prereqs_data = {}
    for topic in goal_set[:5]:  # Limit to first 5 for performance
        try:
            prereq_q = list(p.query(f"all_prerequisites({topic}, Prereqs)"))
            if prereq_q:
                prereqs = [str(x) for x in prereq_q[0]['Prereqs']]
                all_prereqs_data[topic] = prereqs
        except Exception as e:
            print(f"Error getting prerequisites for {topic}: {e}")
            all_prereqs_data[topic] = []

    # 12. STATISTICS AND ANALYTICS
    path_stats = {
        'total_time': total_time,
        'topic_count': len(path_data),
        'difficulty_distribution': defaultdict(int),
        'category_distribution': defaultdict(int)
    }
    
    for item in path_data:
        path_stats['difficulty_distribution'][item['difficulty']] += 1
        path_stats['category_distribution'][item['category']] += 1

    # Enhanced visualization: Multiple charts
    try:
        create_enhanced_visualizations(path_data, goal, path_stats)
    except Exception as e:
        print(f"Error creating visualizations: {e}")
        # Create a simple fallback visualization
        create_simple_visualization(path_data, goal)

    return render_template(
        "result.html",
        goal=goal,
        skills=skills,
        available=time_hours,
        user_level=user_level,
        learning_style=learning_style,
        path_data=path_data,
        total_time=total_time,
        suggestion=suggestion,
        
        # Unification examples
        same_dur_pairs=same_dur_pairs,
        same_diff_pairs=same_diff_pairs,
        
        # Cut
        first_topic=first_topic,
        
        # Negation
        cannot=cannot,
        
        # Arithmetic and List operations
        short_threshold=short_threshold,
        short_topics=short_topics,
        long_topics=long_topics,
        intersection=intersection,
        
        # Quantifiers
        some_topic=some_topic,
        universal_demo_topic=universal_demo_topic,
        all_prereqs_known=all_prereqs_known,
        
        # Recursion
        all_prereqs_data=all_prereqs_data,
        
        path_stats=path_stats,
        
        # Visualization URLs
        img_url=url_for("static", filename="learning_path.png"),
        chart1_url=url_for("static", filename="difficulty_chart.png"),
        chart2_url=url_for("static", filename="category_chart.png"),
        chart3_url=url_for("static", filename="timeline_chart.png"),
    )

def create_enhanced_visualizations(path_data, goal, path_stats):
    """Create multiple enhanced visualizations showcasing Prolog concepts."""
    
    # 1. Enhanced Learning Path Timeline
    img_path = os.path.join("static", "learning_path.png")
    xs = list(range(1, len(path_data) + 1))
    ys = [1] * len(path_data)
    
    plt.figure(figsize=(max(8, len(path_data) * 1.2), 3))
    plt.plot(xs, ys, 'o-', linewidth=3, markersize=8, color='#3b82f6')
    
    for i, item in enumerate(path_data, start=1):
        plt.text(i, 1.05, item['topic'], ha='center', va='bottom', fontsize=9, 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='#1e40af', alpha=0.8))
        plt.text(i, 0.95, f"{item['duration']}h", ha='center', va='top', fontsize=8, color='#6b7280')
    
    plt.title(f"Learning Path: {goal}", fontsize=14, fontweight='bold', color='#1f2937')
    plt.yticks([])
    plt.xticks([])
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    # 2. Difficulty Distribution Chart
    chart1_path = os.path.join("static", "difficulty_chart.png")
    difficulties = list(path_stats['difficulty_distribution'].keys())
    counts = list(path_stats['difficulty_distribution'].values())
    colors = ['#10b981', '#f59e0b', '#ef4444']
    
    plt.figure(figsize=(8, 6))
    bars = plt.bar(difficulties, counts, color=colors[:len(difficulties)], alpha=0.8, edgecolor='white', linewidth=2)
    plt.title(f"Difficulty Distribution for {goal}", fontsize=14, fontweight='bold', color='#1f2937')
    plt.xlabel('Difficulty Level', fontsize=12, color='#374151')
    plt.ylabel('Number of Topics', fontsize=12, color='#374151')
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                str(count), ha='center', va='bottom', fontweight='bold')
    
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(chart1_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    # 3. Category Distribution Chart
    chart2_path = os.path.join("static", "category_chart.png")
    categories = list(path_stats['category_distribution'].keys())
    cat_counts = list(path_stats['category_distribution'].values())
    
    plt.figure(figsize=(10, 6))
    colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
    wedges, texts, autotexts = plt.pie(cat_counts, labels=categories, autopct='%1.1f%%', 
                                       colors=colors, startangle=90, shadow=True)
    
    plt.title(f"Category Distribution for {goal}", fontsize=14, fontweight='bold', color='#1f2937')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig(chart2_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    # 4. Timeline with Duration Chart
    chart3_path = os.path.join("static", "timeline_chart.png")
    topics = [item['topic'] for item in path_data]
    durations = [item['duration'] for item in path_data]
    colors = [item['difficulty'] for item in path_data]
    
    # Map difficulty to colors
    color_map = {'beginner': '#10b981', 'intermediate': '#f59e0b', 'advanced': '#ef4444'}
    color_values = [color_map.get(c, '#6b7280') for c in colors]
    
    plt.figure(figsize=(12, 6))
    bars = plt.barh(topics, durations, color=color_values, alpha=0.8, edgecolor='white', linewidth=1)
    
    plt.title(f"Learning Timeline for {goal}", fontsize=14, fontweight='bold', color='#1f2937')
    plt.xlabel('Duration (hours)', fontsize=12, color='#374151')
    plt.ylabel('Topics', fontsize=12, color='#374151')
    
    # Add duration labels on bars
    for bar, duration in zip(bars, durations):
        plt.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2, 
                f"{duration}h", ha='left', va='center', fontweight='bold')
    
    plt.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(chart3_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

def create_simple_visualization(path_data, goal):
    """Create a simple fallback visualization."""
    img_path = os.path.join("static", "learning_path.png")
    plt.figure(figsize=(8, 4))
    plt.text(0.5, 0.5, "Visualization unavailable", 
             horizontalalignment='center', 
             verticalalignment='center',
             transform=plt.gca().transAxes)
    plt.axis('off')
    plt.savefig(img_path)
    plt.close()
    
@app.route("/backtrack-demo", methods=["GET"])
def backtrack_demo():
    return render_template("backtrack.html")
@app.route("/remove_skill", methods=["POST"])
def remove_skill():
    """Remove a known skill from the user's profile."""
    skill = request.form.get("skill", "").strip().lower()
    if not skill:
        flash("No skill specified to remove.", "error")
        return redirect(url_for("home"))
        
    p = new_prolog()
    try:
        # Try to remove the skill using Prolog retract
        list(p.query(f"retract(known({skill}))"))
        flash(f"Successfully removed skill: {skill}", "success")
    except Exception as e:
        print(f"Error removing skill: {e}")
        flash("Error removing skill. Please try again.", "error")
    
    # Redirect back to previous page or home
    return redirect(request.referrer or url_for("home"))

@app.route("/unlearnable-topics")
def unlearnable_topics():
    """Show topics that can't be learned yet due to missing prerequisites."""
    p = new_prolog()
    
    # Clear any existing known skills
    list(p.query("retractall(known(_))"))
    
    # Get skills from query parameter if provided
    skills_param = request.args.get('skills', '')
    if skills_param:
        skills = [s.strip().lower() for s in skills_param.split(',') if s.strip()]
        for skill in skills:
            p.assertz(f"known({skill})")
    
    # Get all topics
    try:
        topics = list({str(r['Topic']) for r in p.query("topic(Topic, _, _, _, _, _)")})
        unlearnable = []
        
        for topic in topics:
            # Check if topic is unlearnable
            if list(p.query(f"cannot_learn({topic})")):
                # Get missing prerequisites
                missing = list(p.query(f"topic({topic}, Prereqs, _, _, _, _), member(P, Prereqs), \\+ known(P)"))
                if missing:
                    missing_prereqs = list({str(m['P']) for m in missing})
                    unlearnable.append({
                        'topic': topic,
                        'missing_prereqs': missing_prereqs
                    })
        
        return render_template("unlearnable_topics.html", 
                             unlearnable_topics=unlearnable,
                             skills_entered=bool(skills_param))
    
    except Exception as e:
        print(f"Error getting unlearnable topics: {e}")
        flash("Error retrieving unlearnable topics", "error")
        return redirect(url_for("home"))

@app.route("/exhaustive-paths", methods=["POST"])
def exhaustive_paths():
    """Find all possible learning paths with exhaustive backtracking."""
    start_topic = request.form.get("start_topic", "html").strip()
    goal_topic = request.form.get("goal_topic", "react").strip()
    max_depth = int(request.form.get("max_depth", "5"))

    p = new_prolog()
    try:
        paths = list(p.query(f"find_all_paths({start_topic}, {goal_topic}, {max_depth}, Path)"))
        all_paths = []
        for result in paths:
            path = [str(t) for t in result["Path"]]
            all_paths.append(path)

        return render_template(
            "exhaustive_paths.html",
            start_topic=start_topic,
            goal_topic=goal_topic,
            max_depth=max_depth,
            paths=all_paths
        )
    except Exception as e:
        flash(f"Error finding paths: {str(e)}", "error")
        return redirect(url_for("home"))

# -----------------------------
# New routes: A* and AO*
# -----------------------------

@app.route("/astar", methods=["GET", "POST"])
def astar_view():
    if request.method == "GET":
        return render_template_string(
            """
            {% extends 'base.html' %}
            {% block content %}
            <h2>A* Search (Topics Graph)</h2>
            <form method="post" class="space-y-2">
                <label>Start node <input name="start" placeholder="html" required></label>
                <label>Goal node <input name="goal" placeholder="react" required></label>
                <button type="submit">Run A*</button>
            </form>
            <p class="mt-4 text-sm text-gray-600">Graph uses prerequisite edges and goal list adjacency. Heuristic = topic duration.</p>
            {% endblock %}
            """
        )

    start = request.form.get("start", "html").strip().lower()
    goal = request.form.get("goal", "react").strip().lower()

    p = new_prolog()
    try:
        # A*
        ares = list(p.query(f"astar({start}, {goal}, Path, Cost)"))
        if ares:
            apath = [str(t) for t in ares[0]['Path']]
            acost = int(ares[0]['Cost']) if 'Cost' in ares[0] else 0
        else:
            apath, acost = [], 0

        # Uninformed DFS for comparison
        ures = list(p.query(f"uninformed_dfs({start}, {goal}, UPath, UCost, _)"))
        if ures:
            upath = [str(t) for t in ures[0]['UPath']]
            ucost = int(ures[0]['UCost']) if 'UCost' in ures[0] else 0
        else:
            upath, ucost = [], 0

        return render_template_string(
            """
            {% extends 'base.html' %}
            {% block content %}
            <h2>A* Result</h2>
            <p><b>Start</b>: {{start}} &nbsp; <b>Goal</b>: {{goal}}</p>
            <h3 class="mt-3">A*</h3>
            <p><b>Path</b>: {{apath|join(' → ')}}</p>
            <p><b>Cost</b>: {{acost}} &nbsp; <b>Expanded</b>: {{aexp}}</p>
            <h3 class="mt-3">Uninformed DFS</h3>
            <p><b>Path</b>: {{upath|join(' → ')}}</p>
            <p><b>Cost</b>: {{ucost}} &nbsp; <b>Expanded</b>: {{uexp}}</p>
            <a class="mt-4 inline-block" href="{{ url_for('astar_view') }}">Run again</a>
            {% endblock %}
            """,
            start=start, goal=goal,
            apath=apath, acost=acost,
            upath=upath, ucost=ucost
        )
    except Exception as e:
        flash(f"A* error: {e}", "error")
        return redirect(url_for("home"))

@app.route("/aostar", methods=["GET", "POST"])
def aostar_view():
    if request.method == "GET":
        return render_template_string(
            """
            {% extends 'base.html' %}
            {% block content %}
            <h2>AO* Search (AND-OR Graph)</h2>
            <form method="post" class="space-y-2">
                <label>Root node <input name="root" placeholder="frontend_stack" required></label>
                <button type="submit">Run AO*</button>
            </form>
            <p class="mt-4 text-sm text-gray-600">AND-OR alternatives are defined in the knowledge base.</p>
            {% endblock %}
            """
        )

    root = request.form.get("root", "frontend_stack").strip().lower()

    p = new_prolog()
    try:
        res = list(p.query(f"aostar({root}, Strategy, Cost)"))
        if res:
            strategy = [str(t) for t in res[0]['Strategy']]
            cost = int(res[0]['Cost']) if 'Cost' in res[0] else 0
        else:
            strategy, cost = [], 0

        return render_template_string(
            """
            {% extends 'base.html' %}
            {% block content %}
            <h2>AO* Result</h2>
            <p><b>Root</b>: {{root}}</p>
            <p><b>Chosen strategy (AND-set)</b>: {{strategy|join(' + ')}}</p>
            <p><b>Total cost</b>: {{cost}}</p>
            <a class="mt-4 inline-block" href="{{ url_for('aostar_view') }}">Run again</a>
            {% endblock %}
            """,
            root=root, strategy=strategy, cost=cost
        )
    except Exception as e:
        flash(f"AO* error: {e}", "error")
        return redirect(url_for("home"))
    
if __name__ == "__main__":
    app.run(debug=True)
