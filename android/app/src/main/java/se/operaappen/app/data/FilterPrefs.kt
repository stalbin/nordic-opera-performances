package se.operaappen.app.data

import android.content.Context

/** Sparar valda filter mellan gångerna appen öppnas. Tom mängd = alla. */
class FilterPrefs(context: Context) {
    private val prefs = context.getSharedPreferences("filter", Context.MODE_PRIVATE)

    var houses: Set<String>
        get() = prefs.getStringSet("houses", emptySet())!!.toSet()
        set(v) = prefs.edit().putStringSet("houses", v).apply()

    var city: String
        get() = prefs.getString("city", "") ?: ""
        set(v) = prefs.edit().putString("city", v).apply()

    var genres: Set<String>
        get() = prefs.getStringSet("genres", emptySet())!!.toSet()
        set(v) = prefs.edit().putStringSet("genres", v).apply()
}
