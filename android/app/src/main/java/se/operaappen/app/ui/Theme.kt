package se.operaappen.app.ui

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Vinrod = Color(0xFF6B1D2A)
private val VinrodLjus = Color(0xFFE7B6BD)
private val Guld = Color(0xFFB8893B)
private val GuldLjus = Color(0xFFE8C27A)

private val Light = lightColorScheme(
    primary = Vinrod,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFF6DADD),
    onPrimaryContainer = Color(0xFF3E0E17),
    secondary = Guld,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFF7E6C6),
    onSecondaryContainer = Color(0xFF3B2A06),
    tertiaryContainer = Color(0xFFFFE0B8),
    onTertiaryContainer = Color(0xFF4A2800),
    background = Color(0xFFFBF7F2),
    surface = Color(0xFFFBF7F2),
    surfaceVariant = Color(0xFFF1E8E0),
    surfaceContainer = Color(0xFFF5EEE7),
    surfaceContainerHigh = Color(0xFFEFE6DE),
)

private val Dark = darkColorScheme(
    primary = VinrodLjus,
    onPrimary = Color(0xFF4A111C),
    primaryContainer = Color(0xFF5A1823),
    onPrimaryContainer = Color(0xFFFFDADF),
    secondary = GuldLjus,
    onSecondary = Color(0xFF3B2A06),
    secondaryContainer = Color(0xFF574012),
    onSecondaryContainer = Color(0xFFF7E6C6),
    tertiaryContainer = Color(0xFF6A3F00),
    onTertiaryContainer = Color(0xFFFFE0B8),
    background = Color(0xFF1A1416),
    surface = Color(0xFF1A1416),
    surfaceVariant = Color(0xFF2B2224),
    surfaceContainer = Color(0xFF241C1E),
    surfaceContainerHigh = Color(0xFF2E2528),
)

@Composable
fun OperaTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) Dark else Light,
        content = content,
    )
}
