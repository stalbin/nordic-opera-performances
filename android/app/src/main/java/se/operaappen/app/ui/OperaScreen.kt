package se.operaappen.app.ui

import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.clickable
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DateRange
import androidx.compose.material.icons.filled.Place
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.DatePicker
import androidx.compose.material3.DatePickerDialog
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.SelectableDates
import androidx.compose.material3.SuggestionChip
import androidx.compose.material3.rememberDatePickerState
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.pulltorefresh.PullToRefreshBox
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import se.operaappen.app.R
import se.operaappen.app.data.House
import se.operaappen.app.data.Performance
import se.operaappen.app.data.Schedule
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter
import java.time.format.FormatStyle
import java.util.Locale

// Datum formateras på appens språk; mönstret ("EEEE d. MMMM" m.fl.) kommer från strings.xml för varje språk
@Composable
private fun dayFmt(l: Locale, withYear: Boolean) =
    DateTimeFormatter.ofPattern(stringResource(if (withYear) R.string.fmt_day_year else R.string.fmt_day), l)

@Composable
private fun shortFmt(l: Locale, withYear: Boolean) =
    DateTimeFormatter.ofPattern(stringResource(if (withYear) R.string.fmt_short_year else R.string.fmt_short), l)
private fun updatedFmt(l: Locale) = DateTimeFormatter.ofLocalizedDateTime(FormatStyle.MEDIUM, FormatStyle.SHORT).withLocale(l)

@OptIn(ExperimentalMaterial3Api::class, ExperimentalFoundationApi::class)
@Composable
fun OperaScreen(vm: OperaViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val snackbar = remember { SnackbarHostState() }
    var showHouses by rememberSaveable { mutableStateOf(false) }
    var showAbout by rememberSaveable { mutableStateOf(false) }
    var showDate by rememberSaveable { mutableStateOf(false) }
    var searchOpen by rememberSaveable { mutableStateOf(false) }
    val listState = rememberLazyListState()

    LaunchedEffect(state.error, state.schedule != null) {
        val err = state.error
        if (err != null && state.schedule != null) {
            snackbar.showSnackbar(context.getString(errorText(err)))
            vm.dismissError()
        }
    }

    val lang = currentLocale().language

    fun open(p: Performance) {
        val link = p.ticketUrl.ifBlank { p.urlFor(lang) }.ifBlank { state.schedule?.houseById?.get(p.houseId)?.web.orEmpty() }
        if (link.isBlank()) return
        try {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(link)))
        } catch (_: ActivityNotFoundException) {
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.app_name), fontWeight = FontWeight.SemiBold, maxLines = 1, overflow = TextOverflow.Ellipsis) },
                actions = {
                    IconButton(onClick = {
                        if (searchOpen) vm.setQuery("")
                        searchOpen = !searchOpen
                    }) {
                        Icon(
                            if (searchOpen) Icons.Default.Close else Icons.Default.Search,
                            contentDescription = stringResource(if (searchOpen) R.string.cd_search_close else R.string.cd_search_open),
                        )
                    }
                    IconButton(onClick = { showAbout = true }) {
                        Icon(Icons.Default.Info, contentDescription = stringResource(R.string.cd_about))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    actionIconContentColor = MaterialTheme.colorScheme.onPrimary,
                ),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            val schedule = state.schedule
            when {
                schedule == null && state.loading -> Centered { CircularProgressIndicator() }
                schedule == null -> Centered {
                    Text(stringResource(state.error?.let { errorText(it) } ?: R.string.no_performances), Modifier.padding(24.dp))
                    TextButton(onClick = { vm.refresh() }) { Text(stringResource(R.string.retry)) }
                }
                else -> {
                    if (searchOpen) SearchField(state.query, vm::setQuery)
                    CityDateRow(state, onCity = vm::setCity, onDateClick = { showDate = true })
                    FilterRow(
                        schedule = schedule,
                        state = state,
                        onHousesClick = { showHouses = true },
                        onGenre = vm::toggleGenre,
                    )
                    PullToRefreshBox(
                        isRefreshing = state.refreshing,
                        onRefresh = { vm.refresh() },
                        modifier = Modifier.fillMaxSize(),
                    ) {
                        PerformanceList(
                            schedule = schedule,
                            perfs = state.visible,
                            listStateKey = listOf(state.selectedHouses, state.selectedGenres, state.city, state.fromDate),
                            listState = listState,
                            hasFilters = state.filterCount > 0 || state.query.isNotBlank() || state.city.isNotBlank() || state.fromDate != null,
                            onClear = { vm.clearFilters() },
                            onOpen = ::open,
                        )
                    }
                }
            }
        }
    }

    val schedule = state.schedule
    if (showHouses && schedule != null) {
        ModalBottomSheet(onDismissRequest = { showHouses = false }) {
            HouseSheet(schedule.houses, state.selectedHouses, vm::toggleHouse)
        }
    }
    if (showAbout) {
        AboutDialog(schedule, onDismiss = { showAbout = false })
    }
    if (showDate) {
        FromDateDialog(
            current = state.fromDate,
            onPick = { vm.setFromDate(it); showDate = false },
            onDismiss = { showDate = false },
        )
    }
}

@Composable
private fun CityDateRow(state: UiState, onCity: (String) -> Unit, onDateClick: () -> Unit) {
    val focus = LocalFocusManager.current
    val today = LocalDate.now()
    val locale = currentLocale()
    val dateLabel = state.fromDate?.let {
        stringResource(R.string.from_date, shortFmt(locale, it.year != today.year).format(it))
    } ?: stringResource(R.string.from_today)
    Row(
        Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        OutlinedTextField(
            value = state.city,
            onValueChange = onCity,
            modifier = Modifier.weight(1f),
            placeholder = { Text(stringResource(R.string.city_placeholder)) },
            leadingIcon = { Icon(Icons.Default.Place, contentDescription = null) },
            trailingIcon = {
                if (state.city.isNotEmpty()) IconButton(onClick = { onCity(""); focus.clearFocus() }) {
                    Icon(Icons.Default.Clear, contentDescription = stringResource(R.string.cd_all_cities))
                }
            },
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Done),
            keyboardActions = KeyboardActions(onDone = { focus.clearFocus() }),
            shape = RoundedCornerShape(28.dp),
        )
        OutlinedButton(
            onClick = onDateClick,
            modifier = Modifier.height(56.dp),
            contentPadding = PaddingValues(horizontal = 14.dp),
            colors = if (state.fromDate != null) ButtonDefaults.outlinedButtonColors(
                containerColor = MaterialTheme.colorScheme.secondaryContainer,
            ) else ButtonDefaults.outlinedButtonColors(),
        ) {
            Icon(Icons.Default.DateRange, contentDescription = null, modifier = Modifier.width(18.dp))
            Spacer(Modifier.width(6.dp))
            Text(dateLabel, maxLines = 1)
        }
    }
    // Förslag på orter medan man skriver
    val typed = state.city.trim()
    val suggestions = remember(typed, state.schedule) {
        if (typed.isEmpty()) emptyList()
        else state.knownCities.filter { it.foldAccents().contains(typed.foldAccents()) && it.foldAccents() != typed.foldAccents() }.take(8)
    }
    if (suggestions.isNotEmpty()) {
        LazyRow(
            contentPadding = PaddingValues(horizontal = 16.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(suggestions) { c ->
                SuggestionChip(onClick = { onCity(c); focus.clearFocus() }, label = { Text(c) })
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun FromDateDialog(current: LocalDate?, onPick: (LocalDate?) -> Unit, onDismiss: () -> Unit) {
    val today = LocalDate.now()
    val todayUtc = today.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli()
    val pickerState = rememberDatePickerState(
        initialSelectedDateMillis = (current ?: today).atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli(),
        selectableDates = object : SelectableDates {
            override fun isSelectableDate(utcTimeMillis: Long) = utcTimeMillis >= todayUtc
            override fun isSelectableYear(year: Int) = year >= today.year
        },
    )
    DatePickerDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(onClick = {
                val ms = pickerState.selectedDateMillis
                onPick(ms?.let { Instant.ofEpochMilli(it).atZone(ZoneOffset.UTC).toLocalDate() })
            }) { Text(stringResource(R.string.date_show)) }
        },
        dismissButton = {
            TextButton(onClick = { onPick(null) }) { Text(stringResource(R.string.from_today)) }
        },
    ) {
        DatePicker(state = pickerState, title = {
            Text(stringResource(R.string.date_title), Modifier.padding(start = 24.dp, end = 12.dp, top = 16.dp))
        })
    }
}

@Composable
private fun Centered(content: @Composable () -> Unit) {
    Column(
        Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) { content() }
}

@Composable
private fun SearchField(query: String, onChange: (String) -> Unit) {
    OutlinedTextField(
        value = query,
        onValueChange = onChange,
        modifier = Modifier.fillMaxWidth().padding(start = 16.dp, end = 16.dp, top = 12.dp),
        placeholder = { Text(stringResource(R.string.search_placeholder)) },
        leadingIcon = { Icon(Icons.Default.Search, contentDescription = null) },
        trailingIcon = {
            if (query.isNotEmpty()) IconButton(onClick = { onChange("") }) {
                Icon(Icons.Default.Clear, contentDescription = stringResource(R.string.cd_clear_search))
            }
        },
        singleLine = true,
        shape = RoundedCornerShape(28.dp),
    )
}

@Composable
private fun FilterRow(
    schedule: Schedule,
    state: UiState,
    onHousesClick: () -> Unit,
    onGenre: (String) -> Unit,
) {
    val houseLabel = when (state.selectedHouses.size) {
        0 -> stringResource(R.string.all_houses)
        1 -> schedule.houseById[state.selectedHouses.first()]?.name ?: pluralStringResource(R.plurals.n_houses, 1, 1)
        else -> pluralStringResource(R.plurals.n_houses, state.selectedHouses.size, state.selectedHouses.size)
    }
    LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item {
            FilterChip(
                selected = state.selectedHouses.isNotEmpty(),
                onClick = onHousesClick,
                label = { Text(houseLabel) },
                trailingIcon = { Icon(Icons.Default.ArrowDropDown, contentDescription = null, modifier = Modifier.width(18.dp)) },
            )
        }
        items(schedule.genres) { g ->
            FilterChip(
                selected = g in state.selectedGenres,
                onClick = { onGenre(g) },
                label = { Text(genreLabel(g)) },
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = MaterialTheme.colorScheme.secondaryContainer,
                ),
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun PerformanceList(
    schedule: Schedule,
    perfs: List<Performance>,
    listStateKey: Any,
    listState: androidx.compose.foundation.lazy.LazyListState,
    hasFilters: Boolean,
    onClear: () -> Unit,
    onOpen: (Performance) -> Unit,
) {
    LaunchedEffect(listStateKey) { listState.scrollToItem(0) }
    val byDay = remember(perfs) { perfs.groupBy { it.date } }
    val today = LocalDate.now()
    val lang = currentLocale().language

    LazyColumn(state = listState, modifier = Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 24.dp)) {
        if (perfs.isEmpty()) {
            item {
                Column(Modifier.fillMaxWidth().padding(32.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(stringResource(R.string.nothing_matches), style = MaterialTheme.typography.bodyLarge)
                    if (hasFilters) TextButton(onClick = onClear) { Text(stringResource(R.string.show_all)) }
                }
            }
        }
        byDay.forEach { (day, list) ->
            stickyHeader(key = "h$day") { DayHeader(day, today) }
            items(list, key = { it.id }) { p ->
                PerformanceCard(p, schedule.houseById[p.houseId], lang, onOpen)
            }
        }
        item { Footer(schedule) }
    }
}

@Composable
private fun DayHeader(day: LocalDate, today: LocalDate) {
    val locale = currentLocale()
    val text = when (day) {
        today -> stringResource(R.string.today)
        today.plusDays(1) -> stringResource(R.string.tomorrow)
        else -> dayFmt(locale, day.year != today.year).format(day).replaceFirstChar { it.titlecase(locale) }
    }
    Surface(color = MaterialTheme.colorScheme.background, modifier = Modifier.fillMaxWidth()) {
        Text(
            text,
            modifier = Modifier.padding(start = 16.dp, end = 16.dp, top = 14.dp, bottom = 6.dp),
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.primary,
            fontWeight = FontWeight.Bold,
        )
    }
}

@Composable
private fun PerformanceCard(p: Performance, house: House?, lang: String, onOpen: (Performance) -> Unit) {
    val dimmed = p.status == "installt"
    val title = p.titleFor(lang)
    val venue = p.venueFor(lang)
    ElevatedCard(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 4.dp)
            .clickable { onOpen(p) },
    ) {
        Row(Modifier.padding(horizontal = 14.dp, vertical = 10.dp), verticalAlignment = Alignment.Top) {
            Text(
                p.time.ifBlank { "–" },
                modifier = Modifier.width(52.dp),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.primary,
            )
            Column(Modifier.weight(1f)) {
                Text(
                    title,
                    style = MaterialTheme.typography.titleMedium,
                    fontStyle = if (dimmed) FontStyle.Italic else FontStyle.Normal,
                    color = if (dimmed) MaterialTheme.colorScheme.onSurfaceVariant else MaterialTheme.colorScheme.onSurface,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
                val where = listOfNotNull(
                    house?.name,
                    venue.takeIf { it.isNotBlank() && it != house?.name },
                    p.city.takeIf { it.isNotBlank() && it != house?.city && venue.contains(it).not() },
                ).joinToString(" · ")
                if (where.isNotBlank()) {
                    Text(where, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Spacer(Modifier.height(4.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                    Tag(genreLabel(p.genre), MaterialTheme.colorScheme.secondaryContainer, MaterialTheme.colorScheme.onSecondaryContainer)
                    if (p.note.isNotBlank()) Tag(noteLabel(p.note), MaterialTheme.colorScheme.primaryContainer, MaterialTheme.colorScheme.onPrimaryContainer)
                    when (p.status) {
                        "utsalt" -> Tag(stringResource(R.string.status_sold_out), MaterialTheme.colorScheme.surfaceVariant, MaterialTheme.colorScheme.onSurfaceVariant)
                        "installt" -> Tag(stringResource(R.string.status_cancelled), MaterialTheme.colorScheme.errorContainer, MaterialTheme.colorScheme.onErrorContainer)
                        "fa-biljetter" -> Tag(stringResource(R.string.status_few_left), MaterialTheme.colorScheme.tertiaryContainer, MaterialTheme.colorScheme.onTertiaryContainer)
                    }
                }
            }
        }
    }
}

@Composable
private fun Tag(text: String, bg: androidx.compose.ui.graphics.Color, fg: androidx.compose.ui.graphics.Color) {
    Surface(color = bg, contentColor = fg, shape = RoundedCornerShape(6.dp)) {
        Text(text, Modifier.padding(horizontal = 8.dp, vertical = 2.dp), style = MaterialTheme.typography.labelMedium, maxLines = 1)
    }
}

@Composable
private fun Footer(schedule: Schedule) {
    Text(
        stringResource(R.string.footer, formatUpdated(schedule.generated, currentLocale()) ?: stringResource(R.string.unknown)),
        modifier = Modifier.padding(24.dp),
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

private fun formatUpdated(iso: String, locale: Locale): String? =
    runCatching { updatedFmt(locale).format(OffsetDateTime.parse(iso)) }.getOrNull()

private fun errorText(e: LoadError): Int = when (e) {
    LoadError.NO_DATA -> R.string.error_no_data
    LoadError.OFFLINE -> R.string.error_offline
}

@Composable
private fun HouseSheet(houses: List<House>, selected: Set<String>, onToggle: (String) -> Unit) {
    Column(Modifier.verticalScroll(rememberScrollState()).navigationBarsPadding().padding(bottom = 16.dp)) {
        Text(
            stringResource(R.string.choose_houses),
            modifier = Modifier.padding(horizontal = 24.dp, vertical = 8.dp),
            style = MaterialTheme.typography.titleLarge,
        )
        Text(
            if (selected.isEmpty()) stringResource(R.string.none_selected_hint)
            else pluralStringResource(R.plurals.n_selected, selected.size, selected.size),
            modifier = Modifier.padding(horizontal = 24.dp),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(8.dp))
        houses.groupBy { it.country }.forEach { (country, list) ->
            Text(
                countryLabel(country),
                modifier = Modifier.padding(start = 24.dp, end = 24.dp, top = 12.dp, bottom = 2.dp),
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary,
            )
            list.forEach { h -> HouseRow(h, h.id in selected, onToggle) }
        }
    }
}


@Composable
private fun HouseRow(h: House, checked: Boolean, onToggle: (String) -> Unit) {
    Row(
        Modifier.fillMaxWidth().clickable { onToggle(h.id) }.padding(horizontal = 12.dp, vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Checkbox(checked = checked, onCheckedChange = { onToggle(h.id) })
        Column(Modifier.weight(1f)) {
            Text(h.name, style = MaterialTheme.typography.bodyLarge)
            val kind = when (h.season) {
                "sommar" -> stringResource(R.string.season_summer)
                "projekt" -> stringResource(R.string.season_project)
                "distrikt" -> stringResource(R.string.season_district)
                else -> ""
            }
            val sub = listOf(h.city, kind).filter { it.isNotBlank() }.joinToString(" · ")
            Text(sub, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Text(
            if (h.count == 0) stringResource(R.string.none_right_now) else "${h.count}",
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(end = 12.dp),
        )
    }
}

@Composable
private fun AboutDialog(schedule: Schedule?, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = { TextButton(onClick = onDismiss) { Text(stringResource(R.string.close)) } },
        title = { Text(stringResource(R.string.about_title)) },
        text = {
            Column {
                Text(stringResource(R.string.about_text))
                if (schedule != null) {
                    Spacer(Modifier.height(12.dp))
                    HorizontalDivider()
                    Spacer(Modifier.height(8.dp))
                    schedule.houses.forEach { h ->
                        val count = if (h.count == 0) stringResource(R.string.house_none)
                        else pluralStringResource(R.plurals.n_performances, h.count, h.count)
                        Text("${h.name} – $count", style = MaterialTheme.typography.bodySmall)
                    }
                    Spacer(Modifier.height(8.dp))
                    Text(
                        stringResource(R.string.updated, formatUpdated(schedule.generated, currentLocale()) ?: stringResource(R.string.unknown)),
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        },
    )
}
