<?php
// veritabanı bağlantısı
$servername = "localhost"; $username = "root"; $password = "root"; $dbname = "uzmanSistemDB";
$conn = @new mysqli($servername, $username, $password, $dbname);
if ($conn && !$conn->connect_error) {
    $conn->set_charset("utf8mb4");
} else {
    $db_error = "DB bağlantısı kurulamadı.";
}

// Veri temizleme fonksiyonu
function temizle($v) {
    if (!isset($v)) return '';
    if (!is_string($v)) $v = strval($v);
    return htmlspecialchars(trim($v));
}

// POST verileri
$fields = ['mood','age','medication','health','living','social_interaction','family_visits','free_time'];
foreach ($fields as $f) {
    $data[$f] = isset($_POST[$f]) ? temizle($_POST[$f]) : '';
}

// Python scripti çalıştırma
$py = "/usr/bin/env python3";
$script = "/Applications/MAMP/htdocs/Uzman Sistem proje/uzman_sistem.py";
$args = array_map('escapeshellarg', array_values($data));
$cmd = escapeshellcmd($py) . ' ' . escapeshellarg($script) . ' ' . implode(' ', $args);
$des = [0=>["pipe","r"],1=>["pipe","w"],2=>["pipe","w"]];
$proc = proc_open($cmd, $des, $pipes);
$stdout = $stderr = '';
$code = -1;
if (is_resource($proc)) {
    fclose($pipes[0]);
    $stdout = stream_get_contents($pipes[1]); fclose($pipes[1]);
    $stderr = stream_get_contents($pipes[2]); fclose($pipes[2]);
    $code = proc_close($proc);
} else {
    $stderr = "Python başlatılamadı.";
}

// Çıktıyı JSON olarak işle
if ($code === 0) {
    $out = json_decode($stdout, true);
    if (json_last_error() === JSON_ERROR_NONE && is_array($out)) {
        $python_oneri = $out;
    } else {
        $hata = "JSON format hatası.";
    }
} else {
    $hata = "Python hata: " . ($stderr ?: '');
}
if (isset($db_error)) {
    $hata = isset($hata) ? $hata . "\n" . $db_error : $db_error;
}
?>
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Uzman Sistem Sonuç</title>
  <style>
    body {
      font-family: sans-serif;
      margin: 0;
      padding: 0;
      background: url('arkaplan.jpeg') no-repeat center center fixed;
      background-size: cover;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
    }
    .wrapper {
      background: #fff;
      max-width: 800px;
      width: 90%;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    h1 {
      font-size: 2.5em;
      text-align: center;
      margin-bottom: 20px;
      color: #0056b3;
    }
    .section { margin-bottom: 20px; }
    .oneri-box {
      background: #e0f7fa;
      border-left: 4px solid #0277bd;
      padding: 12px;
      border-radius: 4px;
    }
    .oneri-box h2 {
      margin: 0 0 8px;
      color: #01579b;
      font-size: 1.3em;
    }
    .oneri-box p {
      font-size: 2.0em;
      margin: 0;
    }
    .aciklama-box {
      background: #f1f8e9;
      border-left: 4px solid #558b2f;
      padding: 12px;
      border-radius: 4px;
      font-style: italic;
    }
    .aciklama-box p {
      font-size: 1.5em;
      margin: 0;
    }
    .button {
      display: block;
      text-align: center;
      margin: 0 auto;
      padding: 10px 20px;
      text-decoration: none;
      background: #0056b3;
      color: #fff;
      border-radius: 4px;
      width: fit-content;
    }
    pre {
      background: #f4f4f4;
      padding: 10px;
      border-radius: 4px;
      overflow: auto;
    }
  </style>
</head>
<body>
  <div class="wrapper">
    <h1>Uzman Sistem Sonuçları</h1>
    <?php if (!empty($python_oneri)): ?>
      <?php foreach ($python_oneri as $i => $s): ?>
        <?php if (isset($s['text'])): ?>
          <div class="section">
            <div class="oneri-box">
              <h2>Öneri <?= $i+1 ?></h2>
              <p><?= htmlspecialchars($s['text']) ?></p>
            </div>
            <?php if (isset($s['aciklama'])): ?>
              <div class="aciklama-box">
                <p><?= htmlspecialchars($s['aciklama']) ?></p>
              </div>
            <?php endif; ?>
          </div>
        <?php endif; ?>
      <?php endforeach; ?>
    <?php elseif (isset($hata)): ?>
      <div class="section">
        <h2>Hata</h2>
        <pre><?= htmlspecialchars($hata) ?></pre>
      </div>
    <?php else: ?>
      <div class="section">
        <p>Beklenmedik bir durum oluştu.</p>
      </div>
    <?php endif; ?>
    <a href="javascript:history.back()" class="button">Öneri Sistemine Geri Dön</a>
  </div>
</body>
</html>