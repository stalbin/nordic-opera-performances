package se.operaappen.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import se.operaappen.app.ui.OperaScreen
import se.operaappen.app.ui.OperaTheme
import se.operaappen.app.ui.OperaViewModel

class MainActivity : ComponentActivity() {
    private val viewModel: OperaViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            OperaTheme {
                OperaScreen(viewModel)
            }
        }
    }
}
