package se.operaappen.app.data

import org.json.JSONObject
import java.time.LocalDate

data class House(
    val id: String,
    val name: String,
    val city: String,
    val country: String,
    val web: String,
    val season: String,
    val count: Int,
    val status: String,
)

data class Performance(
    val id: String,
    val houseId: String,
    val title: String,
    val date: LocalDate,
    val time: String,
    val genre: String,
    val venue: String,
    val city: String,
    val url: String,
    val ticketUrl: String,
    val status: String,
    val note: String,
    /** Titel, länk och scen på andra språk när operahuset har det, t.ex. {"sv": "Figaros bröllop"}. */
    val titles: Map<String, String> = emptyMap(),
    val urls: Map<String, String> = emptyMap(),
    val venues: Map<String, String> = emptyMap(),
) {
    fun titleFor(lang: String) = pickLang(titles, lang) ?: title
    fun venueFor(lang: String) = pickLang(venues, lang) ?: venue
    fun urlFor(lang: String) = pickLang(urls, lang) ?: url
}

/**
 * Väljer bästa språkversion: appens språk först, sedan närliggande språk
 * (bokmål/nynorsk, och svenska för danska/norska läsare), sedan engelska.
 * null = använd originalet.
 */
fun pickLang(map: Map<String, String>, lang: String): String? {
    if (map.isEmpty()) return null
    val order = when (lang) {
        "nb", "no" -> listOf("nb", "no", "nn", "da", "sv", "en")
        "nn" -> listOf("nn", "nb", "no", "da", "sv", "en")
        "da" -> listOf("da", "nb", "sv", "en")
        "sv" -> listOf("sv", "en")
        "fi" -> listOf("fi", "sv", "en")
        "is" -> listOf("is", "en")
        else -> listOf(lang, "en")
    }
    return order.firstNotNullOfOrNull { map[it]?.takeIf { v -> v.isNotBlank() } }
}

private fun org.json.JSONObject.stringMap(key: String): Map<String, String> {
    val o = optJSONObject(key) ?: return emptyMap()
    return o.keys().asSequence().associateWith { o.optString(it) }.filterValues { it.isNotBlank() }
}

data class Schedule(
    val generated: String,
    val houses: List<House>,
    val genres: List<String>,
    val performances: List<Performance>,
) {
    val houseById: Map<String, House> by lazy { houses.associateBy { it.id } }

    companion object {
        fun parse(json: String): Schedule {
            val root = JSONObject(json)
            val houses = root.optJSONArray("houses")?.let { arr ->
                (0 until arr.length()).map { i ->
                    val h = arr.getJSONObject(i)
                    House(
                        id = h.getString("id"),
                        name = h.optString("name"),
                        city = h.optString("city"),
                        country = h.optString("country", "SE"),
                        web = h.optString("web"),
                        season = h.optString("season"),
                        count = h.optInt("count"),
                        status = h.optString("status"),
                    )
                }
            } ?: emptyList()
            val genres = root.optJSONArray("genres")?.let { arr ->
                (0 until arr.length()).map { arr.getString(it) }
            } ?: emptyList()
            val perfs = root.optJSONArray("performances")?.let { arr ->
                (0 until arr.length()).mapNotNull { i ->
                    val p = arr.getJSONObject(i)
                    val date = runCatching { LocalDate.parse(p.getString("date")) }.getOrNull()
                        ?: return@mapNotNull null
                    Performance(
                        id = p.optString("id"),
                        houseId = p.optString("house"),
                        title = p.optString("title"),
                        date = date,
                        time = p.optString("time"),
                        genre = p.optString("genre", "Övrigt"),
                        venue = p.optString("venue"),
                        city = p.optString("city"),
                        url = p.optString("url"),
                        ticketUrl = p.optString("ticketUrl"),
                        status = p.optString("status"),
                        note = p.optString("note"),
                        titles = p.stringMap("titles"),
                        urls = p.stringMap("urls"),
                        venues = p.stringMap("venues"),
                    )
                }
            }?.distinctBy { it.id } ?: emptyList()
            return Schedule(root.optString("generated"), houses, genres, perfs)
        }
    }
}
