with open(r'templates\dashboard\home.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the admin block and replace it
old = (
    '    {% if current_user.role == \'administrateur\' %}\n'
    '    <!-- Admin Actions -->\n'
    '    <!-- Admin Actions -->\n'
    '    <div class="mb-8 p-6 bg-indigo-50 rounded-xl border border-indigo-100 flex items-center justify-between">\n'
    '        <div>\n'
    '            <h3 class="text-lg font-bold text-indigo-900 mb-1">G\u00e9n\u00e9ration &amp; Validation</h3>\n'
    '            <p class="text-sm text-indigo-700">Validez les emplois du temps g\u00e9n\u00e9r\u00e9s pour les rendre visibles aux\n'
    '                \u00e9tudiants et profs.</p>\n'
    '        </div>\n'
    '        <form action="{{ url_for(\'dashboard.validate_planning\') }}" method="POST"\n'
    '            onsubmit="return confirm(\'\u00cates-vous s\u00fbr de vouloir publier le planning ? Cette action rendra visibles toutes les r\u00e9servations en attente.\');">\n'
    '            <button type="submit"\n'
    '                class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-md flex items-center gap-2 transition-all hover:scale-105 active:scale-95">\n'
    '                <i class="fas fa-check-double"></i>\n'
    '                Valider &amp; Publier\n'
    '            </button>\n'
    '        </form>\n'
    '    </div>\n'
    '    {% endif %}'
)

new = (
    '    {% if current_user.role == \'administrateur\' %}\n'
    '    <!-- Admin Actions -->\n'
    '    <div class="mb-8 p-6 bg-indigo-50 rounded-xl border border-indigo-100 flex items-center justify-between flex-wrap gap-4">\n'
    '        <div>\n'
    '            <h3 class="text-lg font-bold text-indigo-900 mb-1">G\u00e9n\u00e9ration &amp; Validation</h3>\n'
    '            <p class="text-sm text-indigo-700">Validez les emplois du temps g\u00e9n\u00e9r\u00e9s pour les rendre visibles aux\n'
    '                \u00e9tudiants et profs.</p>\n'
    '        </div>\n'
    '        <div class="flex items-center gap-3 flex-wrap">\n'
    '            <a href="{{ url_for(\'dashboard.statistics\') }}"\n'
    '                class="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-md flex items-center gap-2 transition-all hover:scale-105 active:scale-95">\n'
    '                <i class="fas fa-chart-pie"></i>\n'
    '                Voir les statistiques\n'
    '            </a>\n'
    '            <form action="{{ url_for(\'dashboard.validate_planning\') }}" method="POST"\n'
    '                onsubmit="return confirm(\'\u00cates-vous s\u00fbr de vouloir publier le planning ? Cette action rendra visibles toutes les r\u00e9servations en attente.\');">\n'
    '                <button type="submit"\n'
    '                    class="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg shadow-md flex items-center gap-2 transition-all hover:scale-105 active:scale-95">\n'
    '                    <i class="fas fa-check-double"></i>\n'
    '                    Valider &amp; Publier\n'
    '                </button>\n'
    '            </form>\n'
    '        </div>\n'
    '    </div>\n'
    '    {% endif %}'
)

if old in content:
    content = content.replace(old, new)
    with open(r'templates\dashboard\home.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Button added!")
else:
    # Show what we actually have in lines 13-31
    lines = content.split('\n')
    print("NOT FOUND. Lines 13-31:")
    for i in range(12, min(31, len(lines))):
        print(f"  {i+1}: {repr(lines[i])}")
