% Core dynamic predicates
:- dynamic student_goal/1, known/1, time_available/1, user_level/1, learning_style/1.
:- dynamic learning_progress/3.

% Base topic knowledge base
topic(html, [], 5, beginner, frontend, 'HTML fundamentals and semantic markup').
topic(css, [html], 6, beginner, frontend, 'CSS styling and layout techniques').
topic(javascript, [html, css], 8, intermediate, frontend, 'JavaScript programming and DOM manipulation').
topic(react, [javascript], 12, intermediate, frontend, 'React component-based development').
topic(vue, [javascript], 10, intermediate, frontend, 'Vue.js progressive framework').
topic(angular, [javascript, typescript], 15, advanced, frontend, 'Angular enterprise framework').
topic(typescript, [javascript], 6, intermediate, frontend, 'TypeScript type system').
topic(git, [], 4, beginner, tools, 'Version control fundamentals').
topic(github, [git], 3, beginner, tools, 'GitHub collaboration and workflows').
topic(docker, [git], 8, intermediate, tools, 'Containerization and deployment').
topic(kubernetes, [docker], 12, advanced, tools, 'Container orchestration').
topic(uiux, [], 7, beginner, design, 'User interface and experience design').
topic(responsive_design, [css], 6, intermediate, design, 'Mobile-first responsive layouts').
topic(accessibility, [html, css], 5, intermediate, design, 'Web accessibility standards').
topic(algorithms, [], 10, intermediate, backend, 'Algorithm design and analysis').
topic(dsa, [algorithms], 14, intermediate, backend, 'Data structures and algorithms').
topic(system_design, [dsa], 16, advanced, backend, 'Large-scale system architecture').
topic(web_security, [javascript, react], 8, intermediate, security, 'Web security best practices').
topic(authentication, [web_security], 6, intermediate, security, 'User authentication systems').
topic(encryption, [authentication], 8, advanced, security, 'Cryptography and encryption').
topic(python, [], 8, beginner, backend, 'Python programming language').
topic(django, [python], 10, intermediate, backend, 'Django web framework').
topic(flask, [python], 6, intermediate, backend, 'Flask micro-framework').
topic(nodejs, [javascript], 8, intermediate, backend, 'Node.js server-side JavaScript').
topic(express, [nodejs], 6, intermediate, backend, 'Express.js web framework').
topic(database_design, [python], 8, intermediate, backend, 'Database modeling and design').
topic(sql, [database_design], 6, intermediate, backend, 'SQL query language').
topic(mongodb, [javascript], 7, intermediate, backend, 'NoSQL document database').
topic(redis, [python], 5, intermediate, backend, 'In-memory data structure store').
topic(aws, [git], 12, intermediate, cloud, 'Amazon Web Services').
topic(azure, [git], 12, intermediate, cloud, 'Microsoft Azure cloud platform').
topic(ci_cd, [git, docker], 8, intermediate, devops, 'Continuous integration and deployment').
topic(monitoring, [python], 6, intermediate, devops, 'Application monitoring and logging').

% Goal definitions
goal_topics(frontend_dev, [html, css, javascript, responsive_design, react, git, github, accessibility]).
goal_topics(ui_designer, [uiux, html, css, responsive_design, accessibility, github]).
goal_topics(problem_solver, [algorithms, dsa, system_design, python, database_design]).
goal_topics(fullstack_dev, [html, css, javascript, react, python, django, git, github, database_design]).
goal_topics(backend_dev, [python, django, flask, database_design, sql, mongodb, redis, git]).
goal_topics(devops_engineer, [git, docker, kubernetes, aws, ci_cd, monitoring, python]).
goal_topics(security_specialist, [web_security, authentication, encryption, python, javascript, git]).

% Core utility predicates
reset_user_facts :-
    retractall(student_goal(_)),
    retractall(known(_)),
    retractall(time_available(_)),
    retractall(user_level(_)),
    retractall(learning_style(_)).

% Learning path generation
path_to_goal(Goal, OrderedPath) :-
    goal_topics(Goal, Topics),
    findall(K, known(K), KnownSkills),
    build_path(Topics, RawPath0, KnownSkills),
    remove_dups(RawPath0, RawPath),
    filter_known(RawPath, Filtered, KnownSkills),
    OrderedPath = Filtered.

% Core helper predicates
build_path([], [], _).
build_path([T|Rest], Path, Visited) :-
    \+ member(T, Visited),
    topic(T, Prereqs, _, _, _, _),
    build_path(Prereqs, PPath, [T|Visited]),
    build_path(Rest, RPath, [T|Visited]),
    append(PPath, [T|RPath], Path).
build_path([T|Rest], Path, Visited) :-
    member(T, Visited),
    build_path(Rest, Path, Visited).

remove_dups([], []).
remove_dups([H|T], R) :- member(H, T), !, remove_dups(T, R).
remove_dups([H|T], [H|R]) :- \+ member(H, T), remove_dups(T, R).

filter_known([], [], _).
filter_known([H|T], R, Known) :-
    member(H, Known), !, filter_known(T, R, Known).
filter_known([H|T], [H|R], Known) :-
    \+ member(H, Known), filter_known(T, R, Known).

% Topic status and prerequisites
is_topic_complete(Topic) :-
    learning_progress(Topic, complete, _).

cannot_learn(Topic) :-
    topic(Topic, Prereqs, _, _, _, _),
    member(Prereq, Prereqs),
    \+ known(Prereq),
    !.

first_learnable_topic(T) :-
    topic(T, _, _, _, _, _),
    can_learn(T), !.

all_prerequisites_known(Topic) :-
    topic(Topic, Prereqs, _, _, _, _),
    forall(member(P, Prereqs), known(P)).

% Duration-based predicates
short_topics(Threshold, Topic) :-
    topic(Topic, _, D, _, _, _),
    D =< Threshold.

long_topics(Threshold, Topic) :-
    topic(Topic, _, D, _, _, _),
    D > Threshold.

% Learning progress tracking
get_learning_progress(Topic, Progress) :-
    findall(progress_entry(Status, Timestamp), 
            learning_progress(Topic, Status, Timestamp), 
            Progress),
    !.

get_latest_progress(Topic, LatestStatus) :-
    findall(Timestamp-Status, 
            learning_progress(Topic, Status, Timestamp), 
            ProgressList),
    sort(1, @>=, ProgressList, Sorted),
    (   Sorted = [_-Status|_] -> 
        LatestStatus = Status
    ;   
        LatestStatus = 'not_started'
    ),
    !.

% Prerequisite analysis
all_prerequisites(Topic, Prereqs) :-
    topic(Topic, DirectPrereqs, _, _, _, _),
    findall(P, (member(P, DirectPrereqs), all_prerequisites(P, _)), IndirectPrereqs),
    append(DirectPrereqs, IndirectPrereqs, Prereqs).

% Same duration topics in goal path
goal_path_same_duration_topics(Goal, T1, T2) :-
    path_to_goal(Goal, Path),
    member(T1, Path),
    member(T2, Path),
    T1 \= T2,
    topic(T1, _, D, _, _, _),
    topic(T2, _, D, _, _, _).

% Find topics with same difficulty level
same_difficulty_topics(T1, T2) :-
    topic(T1, _, _, Diff, _, _),
    topic(T2, _, _, Diff, _, _),
    T1 \= T2.

% Helper for learning checks
can_learn(Topic) :-
    topic(Topic, Prereqs, _, _, _, _),
    forall(member(P, Prereqs), known(P)).

% Advanced backtracking with exhaustive path finding
% This will try all possible paths even after success

exhaustive_path_find(Start, Goal, MaxDepth, Path) :-
    exhaustive_search(Start, Goal, [Start], Path, MaxDepth, 1).

exhaustive_search(Goal, Goal, CurrentPath, ReversedPath, _, Attempt) :-
    reverse(CurrentPath, ReversedPath),
    format('Success: Found path attempt #~w~n', [Attempt]).

exhaustive_search(Current, Goal, Visited, Path, MaxDepth, Attempt) :-
    MaxDepth > 0,
    NextDepth is MaxDepth - 1,
    topic(Current, _, _, _, _, _),
    (topic(Next, Prerequisites, _, _, _, _),
     member(Current, Prerequisites)),  % Find topics that require current
    \+ member(Next, Visited),
    format('Attempt #~w: Trying ~w -> ~w~n', [Attempt, Current, Next]),
    NextAttempt is Attempt + 1,
    (exhaustive_search(Next, Goal, [Next|Visited], Path, NextDepth, NextAttempt)
    ;  % Backtrack even on success
     format('Backtracking from ~w~n', [Next]),
     fail).

% Helper predicate to find all possible paths
find_all_paths(Start, Goal, MaxDepth, AllPaths) :-
    findall(Path,
            exhaustive_path_find(Start, Goal, MaxDepth, Path),
            AllPaths).

# Add these predicates after your dynamic declarations:

% Skill management predicates
remove_skill(Skill) :-
    retract(known(Skill)),
    !.

remove_skill(_).

% Helper to check if removing a skill would break dependencies
skill_dependencies(Skill, Dependencies) :-
    findall(Topic, (
        known(Topic),
        topic(Topic, Prereqs, _, _, _, _),
        member(Skill, Prereqs)
    ), Dependencies).

safe_to_remove_skill(Skill) :-
    skill_dependencies(Skill, []).

% List intersection predicate
list_intersection([], _, []).
list_intersection([X|Rest], List2, [X|Result]) :-
    member(X, List2),
    list_intersection(Rest, List2, Result).
list_intersection([_|Rest], List2, Result) :-
    list_intersection(Rest, List2, Result).

generate_learning_path(Topic,[Topic],[Topic],Time,Time):-
	can_learn(Topic),
	topic(Topic,[],_,_,_,_).
    
generate_learning_path(Topic,Path,Visited,TimeSpend,MaxTime):-
	can_learn(Topic),
	topic(Topic,Prereqs,Duration,_,_,_).
	NewTime is TimeSpent+Duration.
	NewTime=<MaxTime,
	generate_prereq_paths(Prereqs,[],PrereqPaths,[Topic|Visited],NewTime,MaxTime),
	append(PrereqPaths,[Topic],Path).



% ==========================
% A* and AO* SEARCH ADDITIONS
% ==========================

% Uninformed DFS path for comparison
uninformed_dfs(Start, Goal, Path, Cost, Expanded) :-
    uninformed_dfs_(Start, Goal, [Start], P, 0, Cost, 0, Expanded),
    reverse(P, Path).

uninformed_dfs_(Goal, Goal, Acc, Acc, C, C, E, E1) :-
    E1 is E + 1.

uninformed_dfs_(Current, Goal, Acc, Path, C0, C, E0, E) :-
    edge(Current, Next, W),
    \+ member(Next, Acc),
    C1 is C0 + W,
    E1 is E0 + 1,
    uninformed_dfs_(Next, Goal, [Next|Acc], Path, C1, C, E1, E).
ao_star(Node, [Node], Cost) :-
    leaf_cost(Node, Cost).

% Core web development path
edge(html, css, 6).
edge(html, javascript, 8).
edge(css, responsive_design, 6).
edge(css, javascript, 4).  % Basic CSS helps understand JS DOM manipulation
edge(javascript, react, 12).
edge(javascript, vue, 10).
edge(javascript, angular, 15).
edge(javascript, typescript, 6).
edge(typescript, angular, 8).  % Angular works better with TypeScript

% Frontend build tools
edge(javascript, npm, 3).
edge(npm, webpack, 5).
edge(npm, babel, 4).
edge(webpack, react, 3).  % Need webpack for production React builds
edge(babel, react, 2).    % Need Babel for JSX

% State management
edge(react, redux, 8).
edge(react, context_api, 5).
edge(javascript, redux, 6).  % Can learn Redux with plain JS
edge(typescript, redux, 4).  % TypeScript helps with Redux

% Backend integration
edge(javascript, nodejs, 8).
edge(nodejs, express, 6).
edge(express, rest_api, 8).
edge(nodejs, graphql, 10).
edge(react, graphql, 6).  % React + GraphQL is common
edge(rest_api, graphql, 4).

% Database
edge(javascript, mongodb, 7).
edge(nodejs, mongodb, 5).
edge(sql, orm, 6).
edge(orm, django, 4).
edge(orm, flask, 4).

% Testing
edge(javascript, jest, 5).
edge(react, jest, 3).
edge(javascript, cypress, 6).

% DevOps
edge(git, github, 3).
edge(github, ci_cd, 6).
edge(docker, kubernetes, 12).
edge(nodejs, docker, 5).
edge(docker, aws, 8).

% Add more specific edges for better pathfinding
edge(css, css_frameworks, 4).
edge(css_frameworks, tailwind, 3).
edge(css_frameworks, bootstrap, 2).
edge(tailwind, react, 2).  % Tailwind works well with React
edge(bootstrap, react, 3). % Bootstrap can be used with React

% Update heuristics to reflect topic difficulty
h(html, 5).
h(css, 8).
h(css_frameworks, 4).
h(tailwind, 3).
h(bootstrap, 2).
h(javascript, 15).
h(typescript, 8).
h(react, 20).
h(redux, 10).
h(context_api, 6).
h(nodejs, 12).
h(express, 8).
h(rest_api, 10).
h(graphql, 12).
h(mongodb, 8).
h(sql, 10).
h(orm, 6).
h(jest, 5).
h(cypress, 6).
h(docker, 8).
h(kubernetes, 15).
h(aws, 12).
h(git, 3).
h(github, 2).
h(ci_cd, 6).
h(webpack, 5).
h(babel, 3).
h(npm, 2).

% A* wrapper
astar(Start, Goal, Path, Cost) :-
    h(Start, H0),
    astar_search([node(Start, [Start], 0, H0)], Goal, Path, Cost).

% Expand until goal
astar_search([node(Goal, RevPath, G, _)|_], Goal, Path, G) :-
    reverse(RevPath, Path).

astar_search([node(N, RevPath, G, _)|Rest], Goal, Path, Cost) :-
    findall(node(Child,[Child|RevPath],G1,F1),
            ( edge(N,Child,W),
              \+ member(Child, RevPath),
              G1 is G + W,
              h(Child,H),
              F1 is G1 + H),
            Children),
    append(Rest, Children, Open),
    sort(3, @=<, Open, OpenSorted),   % sort by F = G+H
    astar_search(OpenSorted, Goal, Path, Cost).

% AND-OR graph
andor(frontend, [[html, css, js, react],
                 [html, css, vue],
                 [html, css, ts, angular]]).

% Leaf costs
cost(html, 1).
cost(css, 1).
cost(js, 2).
cost(react, 3).
cost(vue, 2).
cost(ts, 2).
cost(angular, 3).


leaf_cost(N, C) :- cost(N,C), !.
leaf_cost(_,1).

% AO* evaluation
aostar(Node, BestAlt, Cost) :-
    andor(Node, Alts), !,
    findall(C-A,
            ( member(A, Alts),
              maplist(leaf_cost, A, Costs),
              sum_list(Costs, C)),
            Pairs),
    sort(Pairs, [Cost-BestAlt|_]).

aostar(Node, [Node], C) :-
    leaf_cost(Node, C).

