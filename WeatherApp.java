import javax.swing.*;
import java.awt.*;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import org.json.JSONObject;
import org.json.JSONArray;

public class WeatherApp {
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new WeatherApp().buildUI());
    }
	void buildUI() {
        JFrame frame = new JFrame("Weather Forecast");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(700, 500);
        frame.setLayout(new BorderLayout());

        // Top panel - search bar
        JPanel topPanel = new JPanel(new FlowLayout());
        JTextField cityField = new JTextField(20);
        JButton searchBtn = new JButton("Search");
        topPanel.add(new JLabel("City: "));
        topPanel.add(cityField);
        topPanel.add(searchBtn);

        // Center panel - results
        JTextArea resultArea = new JTextArea();
        resultArea.setFont(new Font("Monospaced", Font.PLAIN, 14));
        resultArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(resultArea);

        frame.add(topPanel, BorderLayout.NORTH);
        frame.add(scrollPane, BorderLayout.CENTER);
        frame.setVisible(true);

        // Search button action
        searchBtn.addActionListener(e -> {
            String city = cityField.getText().trim();
            if (!city.isEmpty()) {
                resultArea.setText("Fetching weather for " + city + "...");
                fetchWeather(city, resultArea);
            }
        });
    }

	void fetchWeather(String city, JTextArea resultArea) {
        new Thread(() -> {
            try {
                String url = "http://127.0.0.1:5000/weather?city=" + 
                             city.replace(" ", "%20");

                HttpClient client = HttpClient.newHttpClient();
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .build();

                HttpResponse<String> response = client.send(request,
                        HttpResponse.BodyHandlers.ofString());

                String body = response.body();
                JSONObject json = new JSONObject(body);

                if (json.has("error")) {
                    resultArea.setText("Error: " + json.getString("error"));
                    return;
                }

                StringBuilder sb = new StringBuilder();
                sb.append("City: ").append(json.getString("city")).append("\n\n");

                JSONArray days = json.getJSONArray("days");
                for (int i = 0; i < days.length(); i++) {
                    JSONObject day = days.getJSONObject(i);
                    sb.append("=== ").append(day.getString("label"))
                      .append(" (").append(day.getString("date")).append(") ===\n");

                    JSONArray slots = day.getJSONArray("slots");
                    for (int j = 0; j < slots.length(); j++) {
                        JSONObject slot = slots.getJSONObject(j);
                        sb.append(String.format("  %-15s | %-20s | Temp: %.1f°C | Wind: %.0f km/h | Rain: %d%%\n",
                                slot.getString("slot"),
                                slot.getString("weather"),
                                slot.getDouble("temp"),
                                slot.getDouble("wind"),
                                slot.getInt("rain")));
                    }
                    sb.append("\n");
                }

                SwingUtilities.invokeLater(() -> resultArea.setText(sb.toString()));

            } catch (Exception ex) {
                SwingUtilities.invokeLater(() -> 
                    resultArea.setText("Error: " + ex.getMessage()));
            }
        }).start();
    }
	
}