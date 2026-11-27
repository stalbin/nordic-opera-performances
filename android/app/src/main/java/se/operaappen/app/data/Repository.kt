package se.operaappen.app.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import se.operaappen.app.BuildConfig
import java.io.File
import java.net.HttpURLConnection
import java.net.URL

/**
 * Hämtar spelschemat från GitHub och sparar en kopia i telefonen,
 * så att appen fungerar även utan nät (med senast hämtade data).
 */
class Repository(context: Context) {
    private val cacheFile = File(context.filesDir, "forestallningar.json")

    suspend fun cached(): Schedule? = withContext(Dispatchers.IO) {
        if (!cacheFile.exists()) return@withContext null
        runCatching { Schedule.parse(cacheFile.readText()) }.getOrNull()
    }

    /** Hämtar ny data. Kastar fel om nätet inte fungerar; cachen lämnas då orörd. */
    suspend fun refresh(): Schedule = withContext(Dispatchers.IO) {
        val conn = (URL(BuildConfig.DATA_URL).openConnection() as HttpURLConnection).apply {
            connectTimeout = 15_000
            readTimeout = 20_000
            setRequestProperty("Accept", "application/json")
            useCaches = false
        }
        try {
            if (conn.responseCode != 200) error("Servern svarade ${conn.responseCode}")
            val text = conn.inputStream.bufferedReader(Charsets.UTF_8).use { it.readText() }
            val schedule = Schedule.parse(text) // kontrollera att filen går att läsa innan den sparas
            val tmp = File(cacheFile.parentFile, cacheFile.name + ".tmp")
            tmp.writeText(text)
            tmp.renameTo(cacheFile)
            schedule
        } finally {
            conn.disconnect()
        }
    }
}
