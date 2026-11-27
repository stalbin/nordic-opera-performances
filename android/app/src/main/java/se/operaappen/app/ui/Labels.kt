package se.operaappen.app.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.stringResource
import se.operaappen.app.R
import java.util.Locale

/** Språket appen visas på just nu (telefonens eller det som valts för appen). */
@Composable
@ReadOnlyComposable
fun currentLocale(): Locale = LocalConfiguration.current.locales[0] ?: Locale.getDefault()

/** Datafilen använder svenska genrenamn som nycklar; här visas de på appens språk. */
@Composable
fun genreLabel(key: String): String = when (key) {
    "Opera" -> stringResource(R.string.genre_opera)
    "Operett" -> stringResource(R.string.genre_operetta)
    "Balett/dans" -> stringResource(R.string.genre_dance)
    "Musikal" -> stringResource(R.string.genre_musical)
    "Konsert" -> stringResource(R.string.genre_concert)
    "Barn & unga" -> stringResource(R.string.genre_children)
    "Övrigt" -> stringResource(R.string.genre_other)
    else -> key
}

/** Anteckningar med kända nycklar översätts; fri text från operahusen visas som den är. */
@Composable
fun noteLabel(note: String): String = when {
    note.equals("premiere", ignoreCase = true) || note.equals("premiär", ignoreCase = true) ->
        stringResource(R.string.note_premiere)
    note.startsWith("period:") -> stringResource(R.string.note_period, note.removePrefix("period:"))
    note == "other-organizer" -> stringResource(R.string.note_other_organizer)
    else -> note
}

@Composable
fun countryLabel(code: String): String = when (code) {
    "SE" -> stringResource(R.string.country_se)
    "DK" -> stringResource(R.string.country_dk)
    "NO" -> stringResource(R.string.country_no)
    "FI" -> stringResource(R.string.country_fi)
    "FO" -> stringResource(R.string.country_fo)
    else -> code
}
