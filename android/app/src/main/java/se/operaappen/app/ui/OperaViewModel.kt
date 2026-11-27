package se.operaappen.app.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import se.operaappen.app.data.FilterPrefs
import se.operaappen.app.data.Performance
import se.operaappen.app.data.Repository
import se.operaappen.app.data.Schedule
import java.time.LocalDate

enum class LoadError { NO_DATA, OFFLINE }

data class UiState(
    val schedule: Schedule? = null,
    val loading: Boolean = true,
    val refreshing: Boolean = false,
    val error: LoadError? = null,
    val selectedHouses: Set<String> = emptySet(),   // tom = alla
    val selectedGenres: Set<String> = emptySet(),   // tom = alla
    val query: String = "",
    val city: String = "",                          // ort, tom = alla orter
    val fromDate: LocalDate? = null,                // null = från idag
) {
    val startDate: LocalDate
        get() {
            val today = LocalDate.now()
            val d = fromDate ?: return today
            return if (d.isAfter(today)) d else today
        }

    /** Orter som finns i datan, för förslag under ortsrutan. */
    val knownCities: List<String>
        get() {
            val s = schedule ?: return emptyList()
            val fromPerfs = s.performances.map { it.city }
            return (fromPerfs + s.houses.map { it.city }).filter { it.isNotBlank() }.distinct().sorted()
        }

    /** Föreställningar från idag och framåt som matchar filtren, i tidsordning. */
    val visible: List<Performance>
        get() {
            val s = schedule ?: return emptyList()
            val start = startDate
            val q = query.trim().lowercase()
            val c = city.trim()
            return s.performances.filter { p ->
                !p.date.isBefore(start) &&
                    (c.isEmpty() || matchesCity(p, s.houseById[p.houseId]?.city.orEmpty(), c)) &&
                    (selectedHouses.isEmpty() || p.houseId in selectedHouses) &&
                    (selectedGenres.isEmpty() || p.genre in selectedGenres) &&
                    (q.isEmpty() || p.title.lowercase().contains(q) || p.titles.values.any { it.lowercase().contains(q) } ||
                        (s.houseById[p.houseId]?.name?.lowercase()?.contains(q) == true) ||
                        p.venue.lowercase().contains(q) || p.city.lowercase().contains(q))
            }
        }

    val filterCount: Int get() = selectedHouses.size + selectedGenres.size

    private fun matchesCity(p: Performance, houseCity: String, c: String): Boolean {
        val wanted = cityNames(c)
        fun hit(text: String) = text.foldAccents().let { t -> wanted.any { t.contains(it) } }
        if (hit(p.city) || hit(p.venue) || p.venues.values.any { hit(it) }) return true
        // Saknar föreställningen egen ort gäller husets ort – utom för turnéer
        val onTour = "turne" in p.venue.foldAccents()
        return p.city.isBlank() && !onTour && hit(houseCity)
    }
}

/** Orter med flera namn, så att "Helsinki" hittar Helsingfors och "Copenhagen" København. */
private val CITY_ALIASES = listOf(
    listOf("helsingfors", "helsinki"), listOf("tammerfors", "tampere"), listOf("nyslott", "savonlinna"),
    listOf("uleaborg", "oulu"), listOf("vasa", "vaasa"), listOf("abo", "turku"),
    listOf("kobenhavn", "kopenhamn", "copenhagen", "kaupmannahofn"), listOf("goteborg", "gothenburg"),
    listOf("torshavn", "thorshavn"), listOf("trondheim", "trondhjem"),
)

private fun cityNames(typed: String): List<String> {
    val t = typed.foldAccents()
    val group = CITY_ALIASES.firstOrNull { g -> g.any { it.startsWith(t) || t.startsWith(it) } }
    return if (group != null && t.length >= 3) group + t else listOf(t)
}

/** Gemener utan accenter, så att "goteborg" hittar Göteborg och "kobenhavn" København. */
internal fun String.foldAccents(): String =
    java.text.Normalizer.normalize(lowercase().replace("ø", "o").replace("æ", "ae"), java.text.Normalizer.Form.NFD)
        .replace(Regex("\\p{Mn}+"), "")

class OperaViewModel(app: Application) : AndroidViewModel(app) {
    private val repo = Repository(app)
    private val prefs = FilterPrefs(app)

    private val _state = MutableStateFlow(
        UiState(selectedHouses = prefs.houses, selectedGenres = prefs.genres, city = prefs.city)
    )
    val state: StateFlow<UiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            val cached = repo.cached()
            _state.update { it.copy(schedule = cached, loading = cached == null) }
            refresh(showSpinner = false)
        }
    }

    fun refresh(showSpinner: Boolean = true) {
        viewModelScope.launch {
            if (showSpinner) _state.update { it.copy(refreshing = true) }
            try {
                val fresh = repo.refresh()
                _state.update { it.copy(schedule = fresh, error = null) }
            } catch (e: Exception) {
                _state.update {
                    it.copy(error = if (it.schedule == null) LoadError.NO_DATA else LoadError.OFFLINE)
                }
            } finally {
                _state.update { it.copy(loading = false, refreshing = false) }
            }
        }
    }

    fun toggleHouse(id: String) {
        _state.update {
            val s = it.selectedHouses.toggle(id)
            prefs.houses = s
            it.copy(selectedHouses = s)
        }
    }

    fun toggleGenre(g: String) {
        _state.update {
            val s = it.selectedGenres.toggle(g)
            prefs.genres = s
            it.copy(selectedGenres = s)
        }
    }

    fun clearFilters() {
        prefs.houses = emptySet(); prefs.genres = emptySet(); prefs.city = ""
        _state.update { it.copy(selectedHouses = emptySet(), selectedGenres = emptySet(), city = "", fromDate = null, query = "") }
    }

    fun setQuery(q: String) = _state.update { it.copy(query = q) }

    fun setCity(c: String) {
        prefs.city = c
        _state.update { it.copy(city = c) }
    }

    /** null eller dagens datum = från idag. */
    fun setFromDate(d: LocalDate?) =
        _state.update { it.copy(fromDate = d?.takeIf { day -> day.isAfter(LocalDate.now()) }) }

    fun dismissError() = _state.update { it.copy(error = null) }

    private fun Set<String>.toggle(v: String) = if (v in this) this - v else this + v
}
