<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'

type Language = 'curl' | 'python' | 'js' | 'php' | 'go'

interface LangOption {
  id: Language
  label: string
  icon: string
  badge: string
}

const languages: LangOption[] = [
  { id: 'curl', label: 'cURL', icon: 'pi pi-terminal', badge: 'Bash / CLI' },
  { id: 'python', label: 'Python', icon: 'pi pi-code', badge: 'requests' },
  { id: 'js', label: 'JavaScript', icon: 'pi pi-bolt', badge: 'Node & Fetch' },
  { id: 'php', label: 'PHP', icon: 'pi pi-file-code', badge: 'cURL' },
  { id: 'go', label: 'Go', icon: 'pi pi-cog', badge: 'net/http' },
]

const selectedLang = ref<Language>('curl')
const copiedSnippets = ref<Record<string, boolean>>({})

const apiBaseUrl = computed(() => {
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/v1`
  }
  return 'https://pointqr.com/api/v1'
})

const redocUrl = computed(() => {
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/redoc`
  }
  return '/api/redoc'
})

const swaggerUrl = computed(() => {
  if (typeof window !== 'undefined') {
    return `${window.location.origin}/api/docs`
  }
  return '/api/docs'
})

const asyncExportSnippet = computed(() => `# 1. Enqueue background export job
curl -X POST "${apiBaseUrl.value}/qrcodes/{id}/export/async?format=png" \\
  -H "X-API-Key: pqr_your_key_here"

# 2. Poll job status until COMPLETED
curl -X GET "${apiBaseUrl.value}/qrcodes/jobs/{job_id}" \\
  -H "X-API-Key: pqr_your_key_here"`)

function copyText(key: string, text: string) {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(() => {
      copiedSnippets.value[key] = true
      setTimeout(() => {
        copiedSnippets.value[key] = false
      }, 2000)
    })
  } else {
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    copiedSnippets.value[key] = true
    setTimeout(() => {
      copiedSnippets.value[key] = false
    }, 2000)
  }
}

// Complete, fully-tested code snippet templates for all supported languages
const codeSnippets: Record<string, Record<Language, string>> = {
  // ── 1. Listing QR Codes ──
  list: {
    curl: `curl -X GET "https://pointqr.com/api/v1/qrcodes?page=1&per_page=20" \\
  -H "X-API-Key: pqr_your_api_key_here"`,

    python: `import requests

API_KEY = "pqr_your_api_key_here"
BASE_URL = "https://pointqr.com/api/v1"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Fetch paginated list of your active QR codes
response = requests.get(
    f"{BASE_URL}/qrcodes",
    params={"page": 1, "per_page": 20},
    headers=headers
)
data = response.json()

print(f"Total QR codes: {data['total']}")
for qr in data["items"]:
    print(f"- [{qr['type']}] {qr['title']} (ID: {qr['id']}) | Scans: {qr['scan_count']}")`,

    js: `const API_KEY = 'pqr_your_api_key_here';
const BASE_URL = 'https://pointqr.com/api/v1';

// List user's active QR codes
async function listQRCodes() {
  const response = await fetch(\`\${BASE_URL}/qrcodes?page=1&per_page=20\`, {
    method: 'GET',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
  });

  const data = await response.json();
  console.log(\`Total QR codes: \${data.total}\`);
  data.items.forEach(qr => {
    console.log(\`- \${qr.title} (\${qr.id}) | Scans: \${qr.scan_count}\`);
  });
}

listQRCodes();`,

    php: `<?php
$apiKey = 'pqr_your_api_key_here';
$baseUrl = 'https://pointqr.com/api/v1';

$ch = curl_init("$baseUrl/qrcodes?page=1&per_page=20");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => [
        "X-API-Key: $apiKey",
        "Content-Type: application/json"
    ],
]);

$response = curl_exec($ch);
$data = json_decode($response, true);
curl_close($ch);

echo "Total QR codes: " . $data['total'] . "\\n";
foreach ($data['items'] as $qr) {
    echo "- " . $qr['title'] . " (" . $qr['id'] . ") | Scans: " . $qr['scan_count'] . "\\n";
}`,

    go: `package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

const (
	apiKey  = "pqr_your_api_key_here"
	baseURL = "https://pointqr.com/api/v1"
)

type QRCodeList struct {
	Total int                      \`json:"total"\`
	Items []map[string]interface{} \`json:"items"\`
}

func main() {
	req, _ := http.NewRequest("GET", baseURL+"/qrcodes?page=1&per_page=20", nil)
	req.Header.Set("X-API-Key", apiKey)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var list QRCodeList
	json.Unmarshal(body, &list)

	fmt.Printf("Total QR Codes: %d\\n", list.Total)
	for _, qr := range list.Items {
		fmt.Printf("- %v (ID: %v)\\n", qr["title"], qr["id"])
	}
}`,
  },

  // ── 2. Getting Single QR Code ──
  getSingle: {
    curl: `curl -X GET "https://pointqr.com/api/v1/qrcodes/{qr_id}" \\
  -H "X-API-Key: pqr_your_api_key_here"`,

    python: `import requests

API_KEY = "pqr_your_api_key_here"
BASE_URL = "https://pointqr.com/api/v1"
QR_ID = "c1f7b889-4e08-4177-8fa2-6f296316223f"

response = requests.get(
    f"{BASE_URL}/qrcodes/{QR_ID}",
    headers={"X-API-Key": API_KEY}
)
qr = response.json()
print(f"Title: {qr['title']}, Type: {qr['type']}, Scans: {qr['scan_count']}")`,

    js: `const API_KEY = 'pqr_your_api_key_here';
const BASE_URL = 'https://pointqr.com/api/v1';
const QR_ID = 'c1f7b889-4e08-4177-8fa2-6f296316223f';

const response = await fetch(\`\${BASE_URL}/qrcodes/\${QR_ID}\`, {
  headers: { 'X-API-Key': API_KEY },
});
const qr = await response.json();
console.log('QR details:', qr);`,

    php: `<?php
$apiKey = 'pqr_your_api_key_here';
$baseUrl = 'https://pointqr.com/api/v1';
$qrId = 'c1f7b889-4e08-4177-8fa2-6f296316223f';

$ch = curl_init("$baseUrl/qrcodes/$qrId");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER => ["X-API-Key: $apiKey"]
]);
$qr = json_decode(curl_exec($ch), true);
curl_close($ch);

echo "QR Title: " . $qr['title'] . "\\n";`,

    go: `package main

import (
	"fmt"
	"io"
	"net/http"
)

func main() {
	qrID := "c1f7b889-4e08-4177-8fa2-6f296316223f"
	req, _ := http.NewRequest("GET", "https://pointqr.com/api/v1/qrcodes/"+qrID, nil)
	req.Header.Set("X-API-Key", "pqr_your_api_key_here")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println("QR Details:", string(body))
}`,
  },

  // ── 3. Creating Plain QR Code (Without Visual Title) ──
  createPlain: {
    curl: `curl -X POST "https://pointqr.com/api/v1/qrcodes" \\
  -H "X-API-Key: pqr_your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Minimal Website Link",
    "type": "STATIC",
    "target_url": "https://example.com",
    "design_config": {
      "content": "https://example.com",
      "width": 400,
      "height": 400,
      "dotsOptions": {
        "color": "#1e293b",
        "type": "rounded"
      },
      "backgroundOptions": {
        "color": "#ffffff"
      }
    }
  }'`,

    python: `import requests

API_KEY = "pqr_your_api_key_here"
BASE_URL = "https://pointqr.com/api/v1"

payload = {
    "title": "Minimal Website Link",
    "type": "STATIC",
    "target_url": "https://example.com",
    "design_config": {
        "content": "https://example.com",
        "width": 400,
        "height": 400,
        "dotsOptions": {
            "color": "#1e293b",
            "type": "rounded"
        },
        "backgroundOptions": {
            "color": "#ffffff"
        }
    }
}

response = requests.post(
    f"{BASE_URL}/qrcodes",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json=payload
)
qr = response.json()
print(f"Created QR Code successfully! ID: {qr['id']}")`,

    js: `const API_KEY = 'pqr_your_api_key_here';
const BASE_URL = 'https://pointqr.com/api/v1';

async function createPlainQRCode() {
  const payload = {
    title: 'Minimal Website Link',
    type: 'STATIC',
    target_url: 'https://example.com',
    design_config: {
      content: 'https://example.com',
      width: 400,
      height: 400,
      dotsOptions: {
        color: '#1e293b',
        type: 'rounded',
      },
      backgroundOptions: {
        color: '#ffffff',
      },
    },
  };

  const response = await fetch(\`\${BASE_URL}/qrcodes\`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const qr = await response.json();
  console.log('Created plain QR Code:', qr.id);
  return qr;
}

createPlainQRCode();`,

    php: `<?php
$apiKey = 'pqr_your_api_key_here';
$baseUrl = 'https://pointqr.com/api/v1';

$payload = [
    'title' => 'Minimal Website Link',
    'type' => 'STATIC',
    'target_url' => 'https://example.com',
    'design_config' => [
        'content' => 'https://example.com',
        'width' => 400,
        'height' => 400,
        'dotsOptions' => [
            'color' => '#1e293b',
            'type' => 'rounded'
        ],
        'backgroundOptions' => [
            'color' => '#ffffff'
        ]
    ]
];

$ch = curl_init("$baseUrl/qrcodes");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($payload),
    CURLOPT_HTTPHEADER => [
        "X-API-Key: $apiKey",
        "Content-Type: application/json"
    ]
]);

$response = curl_exec($ch);
$qr = json_decode($response, true);
curl_close($ch);

echo "Created QR Code ID: " . $qr['id'] . "\\n";`,

    go: `package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	payload := map[string]interface{}{
		"title":      "Minimal Website Link",
		"type":       "STATIC",
		"target_url": "https://example.com",
		"design_config": map[string]interface{}{
			"content": "https://example.com",
			"width":   400,
			"height":  400,
			"dotsOptions": map[string]interface{}{
				"color": "#1e293b",
				"type":  "rounded",
			},
			"backgroundOptions": map[string]interface{}{
				"color": "#ffffff",
			},
		},
	}

	jsonBytes, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", "https://pointqr.com/api/v1/qrcodes", bytes.NewBuffer(jsonBytes))
	req.Header.Set("X-API-Key", "pqr_your_api_key_here")
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println("Created QR:", string(body))
}`,
  },

  // ── 4. Creating QR Code With Titles / Labels ──
  createWithTitle: {
    curl: `curl -X POST "https://pointqr.com/api/v1/qrcodes" \\
  -H "X-API-Key: pqr_your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "title": "Table 12 Menu",
    "type": "DYNAMIC",
    "target_url": "https://restaurant.example.com/menu/12",
    "design_config": {
      "width": 500,
      "height": 500,
      "labelTop": {
        "enabled": true,
        "text": "SCAN TO ORDER",
        "fontSize": 18,
        "fontWeight": "bold",
        "color": "#0f172a",
        "align": "center",
        "padding": 10
      },
      "labelBottom": {
        "enabled": true,
        "text": "Table #12 • Free Wi-Fi",
        "fontSize": 13,
        "fontWeight": "normal",
        "color": "#64748b",
        "align": "center",
        "padding": 8
      }
    }
  }'`,

    python: `import requests

API_KEY = "pqr_your_api_key_here"
BASE_URL = "https://pointqr.com/api/v1"

payload = {
    "title": "Table 12 Menu",
    "type": "DYNAMIC",
    "target_url": "https://restaurant.example.com/menu/12",
    "design_config": {
        "width": 500,
        "height": 500,
        "labelTop": {
            "enabled": True,
            "text": "SCAN TO ORDER",
            "fontSize": 18,
            "fontWeight": "bold",
            "color": "#0f172a",
            "align": "center",
            "padding": 10
        },
        "labelBottom": {
            "enabled": True,
            "text": "Table #12 • Free Wi-Fi",
            "fontSize": 13,
            "fontWeight": "normal",
            "color": "#64748b",
            "align": "center",
            "padding": 8
        }
    }
}

response = requests.post(
    f"{BASE_URL}/qrcodes",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json=payload
)
qr = response.json()
print(f"Created QR Code with custom titles: ID {qr['id']}")`,

    js: `const API_KEY = 'pqr_your_api_key_here';
const BASE_URL = 'https://pointqr.com/api/v1';

async function createQRCodeWithTitles() {
  const payload = {
    title: 'Table 12 Menu',
    type: 'DYNAMIC',
    target_url: 'https://restaurant.example.com/menu/12',
    design_config: {
      width: 500,
      height: 500,
      labelTop: {
        enabled: true,
        text: 'SCAN TO ORDER',
        fontSize: 18,
        fontWeight: 'bold',
        color: '#0f172a',
        align: 'center',
        padding: 10,
      },
      labelBottom: {
        enabled: true,
        text: 'Table #12 • Free Wi-Fi',
        fontSize: 13,
        fontWeight: 'normal',
        color: '#64748b',
        align: 'center',
        padding: 8,
      },
    },
  };

  const response = await fetch(\`\${BASE_URL}/qrcodes\`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const qr = await response.json();
  console.log('Created QR with top and bottom titles:', qr.id);
  return qr;
}

createQRCodeWithTitles();`,

    php: `<?php
$apiKey = 'pqr_your_api_key_here';
$baseUrl = 'https://pointqr.com/api/v1';

$payload = [
    'title' => 'Table 12 Menu',
    'type' => 'DYNAMIC',
    'target_url' => 'https://restaurant.example.com/menu/12',
    'design_config' => [
        'width' => 500,
        'height' => 500,
        'labelTop' => [
            'enabled' => true,
            'text' => 'SCAN TO ORDER',
            'fontSize' => 18,
            'fontWeight' => 'bold',
            'color' => '#0f172a',
            'align' => 'center',
            'padding' => 10
        ],
        'labelBottom' => [
            'enabled' => true,
            'text' => 'Table #12 • Free Wi-Fi',
            'fontSize' => 13,
            'fontWeight' => 'normal',
            'color' => '#64748b',
            'align' => 'center',
            'padding' => 8
        ]
    ]
];

$ch = curl_init("$baseUrl/qrcodes");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($payload),
    CURLOPT_HTTPHEADER => [
        "X-API-Key: $apiKey",
        "Content-Type: application/json"
    ]
]);

$response = curl_exec($ch);
$qr = json_decode($response, true);
curl_close($ch);

echo "Created QR with titles: " . $qr['id'] . "\\n";`,

    go: `package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

func main() {
	payload := map[string]interface{}{
		"title":      "Table 12 Menu",
		"type":       "DYNAMIC",
		"target_url": "https://restaurant.example.com/menu/12",
		"design_config": map[string]interface{}{
			"width":  500,
			"height": 500,
			"labelTop": map[string]interface{}{
				"enabled":    true,
				"text":       "SCAN TO ORDER",
				"fontSize":   18,
				"fontWeight": "bold",
				"color":      "#0f172a",
				"align":      "center",
				"padding":    10,
			},
			"labelBottom": map[string]interface{}{
				"enabled":    true,
				"text":       "Table #12 • Free Wi-Fi",
				"fontSize":   13,
				"fontWeight": "normal",
				"color":      "#64748b",
				"align":      "center",
				"padding":    8,
			},
		},
	}

	jsonBytes, _ := json.Marshal(payload)
	req, _ := http.NewRequest("POST", "https://pointqr.com/api/v1/qrcodes", bytes.NewBuffer(jsonBytes))
	req.Header.Set("X-API-Key", "pqr_your_api_key_here")
	req.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	fmt.Println("Created QR with titles:", string(body))
}`,
  },

  // ── 5. Uploading Custom Logos ──
  uploadLogo: {
    curl: `# Step 1: Create the QR Code
QR_ID=$(curl -s -X POST "https://pointqr.com/api/v1/qrcodes" \\
  -H "X-API-Key: pqr_your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Branded Logo QR", "type": "DYNAMIC", "target_url": "https://example.com"}' \\
  | jq -r '.id')

# Step 2: Upload center logo file (PNG, SVG, JPEG, or WebP up to 500 KB)
curl -X POST "https://pointqr.com/api/v1/qrcodes/\${QR_ID}/logo" \\
  -H "X-API-Key: pqr_your_api_key_here" \\
  -F "file=@logo.png"`,

    python: `import requests

API_KEY = "pqr_your_api_key_here"
BASE_URL = "https://pointqr.com/api/v1"

# 1. Create QR code
create_res = requests.post(
    f"{BASE_URL}/qrcodes",
    headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    json={
        "title": "Branded QR Code",
        "type": "DYNAMIC",
        "target_url": "https://example.com"
    }
)
qr_id = create_res.json()["id"]

# 2. Upload center logo image
with open("logo.png", "rb") as logo_file:
    upload_res = requests.post(
        f"{BASE_URL}/qrcodes/{qr_id}/logo",
        headers={"X-API-Key": API_KEY},
        files={"file": ("logo.png", logo_file, "image/png")}
    )

updated_qr = upload_res.json()
print("Logo attached successfully! Logo URL:", updated_qr["design_config"]["imageOptions"]["src"])`,

    js: `import fs from 'node:fs';

const API_KEY = 'pqr_your_api_key_here';
const BASE_URL = 'https://pointqr.com/api/v1';

async function createQRWithLogo() {
  // 1. Create the base QR code
  const createRes = await fetch(\`\${BASE_URL}/qrcodes\`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: 'Branded QR Code',
      type: 'DYNAMIC',
      target_url: 'https://example.com',
    }),
  });
  const { id: qrId } = await createRes.json();

  // 2. Upload the logo file using FormData
  const fileBuffer = fs.readFileSync('logo.png');
  const formData = new FormData();
  formData.append('file', new Blob([fileBuffer], { type: 'image/png' }), 'logo.png');

  const uploadRes = await fetch(\`\${BASE_URL}/qrcodes/\${qrId}/logo\`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY },
    body: formData,
  });

  const updatedQR = await uploadRes.json();
  console.log('Logo attached:', updatedQR.design_config.imageOptions);
}

createQRWithLogo();`,

    php: `<?php
$apiKey = 'pqr_your_api_key_here';
$baseUrl = 'https://pointqr.com/api/v1';

// 1. Create QR code
$ch = curl_init("$baseUrl/qrcodes");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode([
        'title' => 'Branded QR Code',
        'type' => 'DYNAMIC',
        'target_url' => 'https://example.com'
    ]),
    CURLOPT_HTTPHEADER => ["X-API-Key: $apiKey", "Content-Type: application/json"]
]);
$qr = json_decode(curl_exec($ch), true);
$qrId = $qr['id'];
curl_close($ch);

// 2. Upload logo via multipart/form-data
$ch = curl_init("$baseUrl/qrcodes/$qrId/logo");
$file = new CURLFile('logo.png', 'image/png', 'logo.png');

curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => ['file' => $file],
    CURLOPT_HTTPHEADER => ["X-API-Key: $apiKey"]
]);

$response = curl_exec($ch);
$updatedQr = json_decode($response, true);
curl_close($ch);

echo "Logo attached successfully!\\n";`,

    go: `package main

import (
	"bytes"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
)

func uploadLogo(qrID string) {
	// Prepare multipart form data
	var b bytes.Buffer
	w := multipart.NewWriter(&b)

	fw, _ := w.CreateFormFile("file", "logo.png")
	file, _ := os.Open("logo.png")
	defer file.Close()
	io.Copy(fw, file)
	w.Close()

	url := fmt.Sprintf("https://pointqr.com/api/v1/qrcodes/%s/logo", qrID)
	req, _ := http.NewRequest("POST", url, &b)
	req.Header.Set("X-API-Key", "pqr_your_api_key_here")
	req.Header.Set("Content-Type", w.FormDataContentType())

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	fmt.Println("Upload status code:", resp.StatusCode)
}

func main() {
	uploadLogo("c1f7b889-4e08-4177-8fa2-6f296316223f")
}`,
  },

  // ── 6. Downloading QR Code ──
  download: {
    curl: `# Export and download high-resolution PNG, SVG, PDF, or EPS
curl -X POST "https://pointqr.com/api/v1/qrcodes/{qr_id}/export?format=png" \\
  -H "X-API-Key: pqr_your_api_key_here" \\
  --output "qrcode.png"

# For vector SVG:
# curl -X POST "https://pointqr.com/api/v1/qrcodes/{qr_id}/export?format=svg" ... --output "qrcode.svg"`,

    python: `import requests

API_KEY = "pqr_your_api_key_here"
BASE_URL = "https://pointqr.com/api/v1"
QR_ID = "c1f7b889-4e08-4177-8fa2-6f296316223f"

# Choose format: 'png', 'svg', 'pdf', or 'eps'
FORMAT = "png"

response = requests.post(
    f"{BASE_URL}/qrcodes/{QR_ID}/export",
    params={"format": FORMAT},
    headers={"X-API-Key": API_KEY}
)

if response.status_code == 200:
    filename = f"exported_qr.{FORMAT}"
    with open(filename, "wb") as f:
        f.write(response.content)
    print(f"Downloaded and saved high-resolution {filename} successfully!")
else:
    print(f"Export failed: {response.status_code} - {response.text}")`,

    js: `import fs from 'node:fs';

const API_KEY = 'pqr_your_api_key_here';
const BASE_URL = 'https://pointqr.com/api/v1';
const QR_ID = 'c1f7b889-4e08-4177-8fa2-6f296316223f';

async function downloadQRCode(format = 'png') {
  const response = await fetch(\`\${BASE_URL}/qrcodes/\${QR_ID}/export?format=\${format}\`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
    },
  });

  if (!response.ok) {
    throw new Error(\`Download failed: \${response.statusText}\`);
  }

  // Stream binary bytes and save to local file
  const arrayBuffer = await response.arrayBuffer();
  const filename = \`qrcode.\${format}\`;
  fs.writeFileSync(filename, Buffer.from(arrayBuffer));
  console.log(\`Successfully saved \${filename}\`);
}

downloadQRCode('png');`,

    php: `<?php
$apiKey = 'pqr_your_api_key_here';
$baseUrl = 'https://pointqr.com/api/v1';
$qrId = 'c1f7b889-4e08-4177-8fa2-6f296316223f';
$format = 'png'; // png, svg, pdf, or eps

$ch = curl_init("$baseUrl/qrcodes/$qrId/export?format=$format");
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_POST => true,
    CURLOPT_HTTPHEADER => ["X-API-Key: $apiKey"]
]);

$data = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode === 200) {
    file_put_contents("qrcode.$format", $data);
    echo "Saved qrcode.$format successfully!\\n";
} else {
    echo "Failed to export with HTTP code $httpCode\\n";
}`,

    go: `package main

import (
	"fmt"
	"io"
	"net/http"
	"os"
)

func main() {
	qrID := "c1f7b889-4e08-4177-8fa2-6f296316223f"
	format := "png" // "png", "svg", "pdf", "eps"

	url := fmt.Sprintf("https://pointqr.com/api/v1/qrcodes/%s/export?format=%s", qrID, format)
	req, _ := http.NewRequest("POST", url, nil)
	req.Header.Set("X-API-Key", "pqr_your_api_key_here")

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusOK {
		outFile, _ := os.Create("downloaded_qr." + format)
		defer outFile.Close()
		io.Copy(outFile, resp.Body)
		fmt.Printf("Successfully saved downloaded_qr.%s\\n", format)
	} else {
		fmt.Printf("Export failed with status: %d\\n", resp.StatusCode)
	}
}`,
  },
}
</script>

<template>
  <div class="api-docs-container max-w-5xl mx-auto pb-16 space-y-10">

    <!-- ── Hero / Overview ──────────────────────────────────────── -->
    <div class="flex flex-col gap-4">
      <div class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary-500">
        <i class="pi pi-code" />
        <span>Developer Reference</span>
      </div>
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 class="text-3xl font-extrabold text-surface-900 dark:text-surface-0 tracking-tight">
            PointQR REST API Documentation
          </h1>
          <p class="text-surface-600 dark:text-surface-400 mt-1 max-w-2xl leading-relaxed text-sm">
            Programmatically create, manage, style, and download QR codes. Integrate custom titles,
            branded logos, scan tracking, and high-resolution vector exports into your applications.
          </p>
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <a
            :href="redocUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm text-white shadow-sm transition-all transform hover:-translate-y-0.5"
            style="background: linear-gradient(135deg, var(--color-primary) 0%, #4f46e5 100%)"
          >
            <i class="pi pi-external-link" />
            <span>Interactive ReDoc</span>
          </a>
          <a
            :href="swaggerUrl"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm border transition-colors"
            style="background: var(--bg-card); border-color: var(--border); color: var(--text-primary)"
          >
            <i class="pi pi-play" />
            <span>Swagger UI</span>
          </a>
        </div>
      </div>
    </div>

    <!-- ── Quick Nav & API Base Card ────────────────────────────── -->
    <div
      class="rounded-2xl border p-6 shadow-sm transition-colors"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
        <!-- API Base URL -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-surface-500">API Base URL</span>
            <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium">v1 Active</span>
          </div>
          <div
            class="flex items-center justify-between rounded-lg px-3 py-2 border font-mono text-sm"
            style="background-color: var(--bg-elevated); border-color: var(--border)"
          >
            <span class="truncate text-surface-800 dark:text-surface-200">{{ apiBaseUrl }}</span>
            <button
              @click="copyText('base-url', apiBaseUrl)"
              class="ml-2 px-2 py-1 text-xs rounded hover:bg-black/5 dark:hover:bg-white/10 transition-colors flex items-center gap-1"
              :title="copiedSnippets['base-url'] ? 'Copied!' : 'Copy Base URL'"
            >
              <i :class="copiedSnippets['base-url'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
              <span class="text-xs">{{ copiedSnippets['base-url'] ? 'Copied' : 'Copy' }}</span>
            </button>
          </div>
        </div>

        <!-- Authentication & Key Link -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-surface-500">Authentication</span>
            <RouterLink
              to="/api-keys"
              class="text-xs font-semibold text-primary-500 hover:text-primary-600 flex items-center gap-1"
            >
              <span>Manage API Keys</span>
              <i class="pi pi-arrow-right text-[10px]" />
            </RouterLink>
          </div>
          <div
            class="flex items-center justify-between rounded-lg px-3 py-2 border font-mono text-sm"
            style="background-color: var(--bg-elevated); border-color: var(--border)"
          >
            <span class="truncate text-surface-800 dark:text-surface-200">X-API-Key: pqr_••••••••••••</span>
            <span class="text-xs text-surface-400">Header</span>
          </div>
        </div>
      </div>

      <!-- Quick Jump Anchors -->
      <div class="mt-6 pt-4 border-t flex flex-wrap gap-2 items-center text-xs" style="border-color: var(--border)">
        <span class="font-semibold text-surface-500 mr-1">Jump to:</span>
        <a href="#auth" class="px-2.5 py-1 rounded-md border hover:border-primary-500 transition-colors" style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-secondary)">Authentication</a>
        <a href="#list-codes" class="px-2.5 py-1 rounded-md border hover:border-primary-500 transition-colors" style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-secondary)">List & Show QR Codes</a>
        <a href="#create-no-title" class="px-2.5 py-1 rounded-md border hover:border-primary-500 transition-colors" style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-secondary)">Create without Title</a>
        <a href="#create-with-title" class="px-2.5 py-1 rounded-md border hover:border-primary-500 transition-colors" style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-secondary)">Create with Title</a>
        <a href="#custom-logo" class="px-2.5 py-1 rounded-md border hover:border-primary-500 transition-colors" style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-secondary)">Custom Logos</a>
        <a href="#download-api" class="px-2.5 py-1 rounded-md border hover:border-primary-500 transition-colors" style="background: var(--bg-elevated); border-color: var(--border); color: var(--text-secondary)">Download & Export</a>
      </div>
    </div>

    <!-- ── Language Selector Bar ────────────────────────────────── -->
    <div
      class="sticky top-4 z-20 rounded-xl border p-2 shadow-md backdrop-blur-md flex items-center justify-between flex-wrap gap-2"
      style="background-color: var(--bg-card); border-color: var(--border)"
    >
      <div class="flex items-center gap-2 pl-2">
        <i class="pi pi-sliders-h text-primary-500 text-sm" />
        <span class="text-xs font-bold uppercase tracking-wider text-surface-600 dark:text-surface-300">Code Language:</span>
      </div>
      <div class="flex items-center gap-1 flex-wrap">
        <button
          v-for="lang in languages"
          :key="lang.id"
          @click="selectedLang = lang.id"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
          :class="[
            selectedLang === lang.id
              ? 'bg-primary-500 text-white shadow-sm'
              : 'hover:bg-black/5 dark:hover:bg-white/5 text-surface-600 dark:text-surface-400'
          ]"
        >
          <i :class="lang.icon" class="text-xs" />
          <span>{{ lang.label }}</span>
          <span
            class="text-[10px] px-1 py-0.2 rounded font-normal opacity-85"
            :class="selectedLang === lang.id ? 'bg-white/20' : 'bg-surface-200 dark:bg-surface-800'"
          >
            {{ lang.badge }}
          </span>
        </button>
      </div>
    </div>

    <!-- ── Section 1: Authentication & Headers ─────────────────── -->
    <section id="auth" class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold text-sm">1</span>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Authentication & Rate Limits</h2>
          <p class="text-xs text-surface-500">How to authenticate requests and stay within rate limits</p>
        </div>
      </div>

      <div
        class="rounded-xl border p-5 space-y-4"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <p class="text-sm text-surface-700 dark:text-surface-300 leading-relaxed">
          All API requests require authentication. Pass your secret key in the
          <code class="px-1.5 py-0.5 rounded text-xs font-mono font-bold" style="background: var(--bg-elevated)">X-API-Key</code>
          HTTP header. Alternatively, web sessions can supply an
          <code class="px-1.5 py-0.5 rounded text-xs font-mono" style="background: var(--bg-elevated)">Authorization: Bearer &lt;JWT&gt;</code> token.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="rounded-lg p-3.5 border transition-colors shadow-sm" style="background-color: var(--bg-card); border-color: var(--border)">
            <span class="text-xs font-medium" style="color: var(--text-secondary)">Create QR Rate Limit</span>
            <p class="text-lg font-bold mt-0.5 tracking-tight" style="color: var(--text-primary)">30 / minute</p>
          </div>
          <div class="rounded-lg p-3.5 border transition-colors shadow-sm" style="background-color: var(--bg-card); border-color: var(--border)">
            <span class="text-xs font-medium" style="color: var(--text-secondary)">Export / Download Limit</span>
            <p class="text-lg font-bold mt-0.5 tracking-tight" style="color: var(--text-primary)">20 / minute</p>
          </div>
          <div class="rounded-lg p-3.5 border transition-colors shadow-sm" style="background-color: var(--bg-card); border-color: var(--border)">
            <span class="text-xs font-medium" style="color: var(--text-secondary)">Logo Upload Limit</span>
            <p class="text-lg font-bold mt-0.5 tracking-tight" style="color: var(--text-primary)">10 / minute</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Section 2: Showing & Listing QR Codes ────────────────── -->
    <section id="list-codes" class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold text-sm">2</span>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Listing & Showing QR Codes</h2>
          <p class="text-xs text-surface-500">Fetch your active QR codes with scan metrics or retrieve a single code</p>
        </div>
      </div>

      <!-- Tab A: List All QR Codes -->
      <div
        class="rounded-xl border overflow-hidden shadow-sm"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <div
          class="flex items-center justify-between px-4 py-3 border-b text-xs font-mono"
          style="background-color: var(--bg-elevated); border-color: var(--border)"
        >
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded font-bold bg-blue-500/20 text-blue-600 dark:text-blue-400">GET</span>
            <span class="text-surface-700 dark:text-surface-300">/api/v1/qrcodes?page=1&per_page=20</span>
          </div>
          <button
            @click="copyText('list-qr', codeSnippets.list[selectedLang])"
            class="flex items-center gap-1 px-2.5 py-1 rounded border hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            style="border-color: var(--border)"
          >
            <i :class="copiedSnippets['list-qr'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
            <span class="font-sans">{{ copiedSnippets['list-qr'] ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>

        <pre
          class="p-4 text-xs font-mono overflow-x-auto leading-relaxed"
          style="background-color: var(--bg-card); color: var(--text-primary)"
        ><code>{{ codeSnippets.list[selectedLang] }}</code></pre>

        <!-- Response Preview -->
        <div class="p-4 border-t text-xs" style="border-color: var(--border); background-color: var(--bg-elevated)">
          <div class="flex items-center justify-between mb-2">
            <span class="font-bold uppercase tracking-wider text-surface-500 text-[11px]">Example List JSON Response (200 OK)</span>
          </div>
          <pre class="font-mono text-surface-700 dark:text-surface-300 overflow-x-auto"><code>{
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1,
  "items": [
    {
      "id": "c1f7b889-4e08-4177-8fa2-6f296316223f",
      "user_id": "84896253-157d-45db-9c3f-2ad5e2eb271e",
      "title": "Main Store Wi-Fi",
      "type": "DYNAMIC",
      "short_code": "k9xL2a1Z",
      "target_url": "https://pointqr.com/welcome",
      "design_config": { ... },
      "is_active": true,
      "scan_count": 48,
      "created_at": "2026-10-14T10:00:00Z",
      "updated_at": "2026-10-14T12:30:00Z"
    }
  ]
}</code></pre>
        </div>
      </div>

      <!-- Tab B: Get Single QR Code -->
      <div
        class="rounded-xl border overflow-hidden shadow-sm"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <div
          class="flex items-center justify-between px-4 py-3 border-b text-xs font-mono"
          style="background-color: var(--bg-elevated); border-color: var(--border)"
        >
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded font-bold bg-blue-500/20 text-blue-600 dark:text-blue-400">GET</span>
            <span class="text-surface-700 dark:text-surface-300">/api/v1/qrcodes/{id}</span>
          </div>
          <button
            @click="copyText('get-single', codeSnippets.getSingle[selectedLang])"
            class="flex items-center gap-1 px-2.5 py-1 rounded border hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            style="border-color: var(--border)"
          >
            <i :class="copiedSnippets['get-single'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
            <span class="font-sans">{{ copiedSnippets['get-single'] ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>

        <pre
          class="p-4 text-xs font-mono overflow-x-auto leading-relaxed"
          style="background-color: var(--bg-card); color: var(--text-primary)"
        ><code>{{ codeSnippets.getSingle[selectedLang] }}</code></pre>
      </div>
    </section>

    <!-- ── Section 3: Creating QR Code without Visual Titles ────── -->
    <section id="create-no-title" class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold text-sm">3</span>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Create QR Code (Without Visual Title)</h2>
          <p class="text-xs text-surface-500">Minimal, clean QR code with no top or bottom text banners</p>
        </div>
      </div>

      <div
        class="rounded-xl border overflow-hidden shadow-sm"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <div
          class="flex items-center justify-between px-4 py-3 border-b text-xs font-mono"
          style="background-color: var(--bg-elevated); border-color: var(--border)"
        >
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">POST</span>
            <span class="text-surface-700 dark:text-surface-300">/api/v1/qrcodes</span>
          </div>
          <button
            @click="copyText('create-plain', codeSnippets.createPlain[selectedLang])"
            class="flex items-center gap-1 px-2.5 py-1 rounded border hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            style="border-color: var(--border)"
          >
            <i :class="copiedSnippets['create-plain'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
            <span class="font-sans">{{ copiedSnippets['create-plain'] ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>

        <pre
          class="p-4 text-xs font-mono overflow-x-auto leading-relaxed"
          style="background-color: var(--bg-card); color: var(--text-primary)"
        ><code>{{ codeSnippets.createPlain[selectedLang] }}</code></pre>
      </div>
    </section>

    <!-- ── Section 4: Creating QR Code with Titles ──────────────── -->
    <section id="create-with-title" class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold text-sm">4</span>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Create QR Code (With Visual Titles / Banners)</h2>
          <p class="text-xs text-surface-500">
            Use <code class="font-mono text-primary-500">labelTop</code> and <code class="font-mono text-primary-500">labelBottom</code>
            to render printed text labels like "SCAN ME" or instructions above/below the barcode
          </p>
        </div>
      </div>

      <div
        class="rounded-xl border overflow-hidden shadow-sm"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <div
          class="flex items-center justify-between px-4 py-3 border-b text-xs font-mono"
          style="background-color: var(--bg-elevated); border-color: var(--border)"
        >
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded font-bold bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">POST</span>
            <span class="text-surface-700 dark:text-surface-300">/api/v1/qrcodes (with labelTop & labelBottom)</span>
          </div>
          <button
            @click="copyText('create-title', codeSnippets.createWithTitle[selectedLang])"
            class="flex items-center gap-1 px-2.5 py-1 rounded border hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            style="border-color: var(--border)"
          >
            <i :class="copiedSnippets['create-title'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
            <span class="font-sans">{{ copiedSnippets['create-title'] ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>

        <pre
          class="p-4 text-xs font-mono overflow-x-auto leading-relaxed"
          style="background-color: var(--bg-card); color: var(--text-primary)"
        ><code>{{ codeSnippets.createWithTitle[selectedLang] }}</code></pre>

        <div class="p-4 border-t text-xs space-y-2" style="border-color: var(--border); background-color: var(--bg-elevated)">
          <p class="font-semibold text-xs" style="color: var(--text-primary)">Customizable Label Properties:</p>
          <ul class="list-disc list-inside space-y-1" style="color: var(--text-secondary)">
            <li><code class="font-mono text-primary-500 font-semibold">fontSize</code> (6–96 px, default: 14)</li>
            <li><code class="font-mono text-primary-500 font-semibold">fontWeight</code> ("normal" | "bold")</li>
            <li><code class="font-mono text-primary-500 font-semibold">align</code> ("center" | "left" | "right")</li>
            <li><code class="font-mono text-primary-500 font-semibold">color</code> (Hex color string e.g. "#111827")</li>
            <li><code class="font-mono text-primary-500 font-semibold">padding</code> (spacing between label and barcode, default: 8 px)</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ── Section 5: Custom Logos ──────────────────────────────── -->
    <section id="custom-logo" class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold text-sm">5</span>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Embed Custom Logos</h2>
          <p class="text-xs text-surface-500">
            Upload your company or brand logo directly into the center of the QR code (PNG, SVG, JPEG, WebP)
          </p>
        </div>
      </div>

      <div
        class="rounded-xl border overflow-hidden shadow-sm"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <div
          class="flex items-center justify-between px-4 py-3 border-b text-xs font-mono"
          style="background-color: var(--bg-elevated); border-color: var(--border)"
        >
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded font-bold bg-amber-500/20 text-amber-600 dark:text-amber-400">POST (multipart/form-data)</span>
            <span class="text-surface-700 dark:text-surface-300">/api/v1/qrcodes/{id}/logo</span>
          </div>
          <button
            @click="copyText('logo-upload', codeSnippets.uploadLogo[selectedLang])"
            class="flex items-center gap-1 px-2.5 py-1 rounded border hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            style="border-color: var(--border)"
          >
            <i :class="copiedSnippets['logo-upload'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
            <span class="font-sans">{{ copiedSnippets['logo-upload'] ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>

        <pre
          class="p-4 text-xs font-mono overflow-x-auto leading-relaxed"
          style="background-color: var(--bg-card); color: var(--text-primary)"
        ><code>{{ codeSnippets.uploadLogo[selectedLang] }}</code></pre>

        <div class="p-4 border-t text-xs space-y-2" style="border-color: var(--border); background-color: var(--bg-elevated)">
          <p class="font-semibold text-xs" style="color: var(--text-primary)">Logo Guidelines & Specs:</p>
          <p class="leading-relaxed" style="color: var(--text-secondary)">
            • Maximum file size: <strong style="color: var(--text-primary)">500 KB</strong>.<br>
            • Supported formats: <strong style="color: var(--text-primary)">PNG, SVG, JPEG, WebP</strong>.<br>
            • The QR code generator automatically sets error correction to level <strong style="color: var(--text-primary)">H (High - 30% recovery)</strong> and creates a protective buffer margin around your logo.
          </p>
        </div>
      </div>
    </section>

    <!-- ── Section 6: Downloading & Exporting ────────────────────── -->
    <section id="download-api" class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold text-sm">6</span>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Download & Export via API</h2>
          <p class="text-xs text-surface-500">
            Stream high-resolution print-ready files directly (<code class="font-mono text-primary-500">png</code>,
            <code class="font-mono text-primary-500">svg</code>, <code class="font-mono text-primary-500">pdf</code>, or <code class="font-mono text-primary-500">eps</code>)
          </p>
        </div>
      </div>

      <div
        class="rounded-xl border overflow-hidden shadow-sm"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <div
          class="flex items-center justify-between px-4 py-3 border-b text-xs font-mono"
          style="background-color: var(--bg-elevated); border-color: var(--border)"
        >
          <div class="flex items-center gap-2">
            <span class="px-2 py-0.5 rounded font-bold bg-purple-500/20 text-purple-600 dark:text-purple-400">POST (Stream)</span>
            <span class="text-surface-700 dark:text-surface-300">/api/v1/qrcodes/{id}/export?format=png</span>
          </div>
          <button
            @click="copyText('download-qr', codeSnippets.download[selectedLang])"
            class="flex items-center gap-1 px-2.5 py-1 rounded border hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
            style="border-color: var(--border)"
          >
            <i :class="copiedSnippets['download-qr'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
            <span class="font-sans">{{ copiedSnippets['download-qr'] ? 'Copied' : 'Copy' }}</span>
          </button>
        </div>

        <pre
          class="p-4 text-xs font-mono overflow-x-auto leading-relaxed"
          style="background-color: var(--bg-card); color: var(--text-primary)"
        ><code>{{ codeSnippets.download[selectedLang] }}</code></pre>

        <div class="p-4 border-t text-xs space-y-2" style="border-color: var(--border); background-color: var(--bg-elevated)">
          <p class="font-semibold text-xs" style="color: var(--text-primary)">Export Formats & Content-Types:</p>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div
              class="p-3 rounded-lg border transition-colors shadow-sm"
              style="background-color: var(--bg-card); border-color: var(--border)"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-sm tracking-wide" style="color: var(--text-primary)">PNG</span>
                <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-600 dark:text-purple-400">Raster</span>
              </div>
              <p class="text-xs font-mono mt-1.5" style="color: var(--text-secondary)">image/png</p>
            </div>
            <div
              class="p-3 rounded-lg border transition-colors shadow-sm"
              style="background-color: var(--bg-card); border-color: var(--border)"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-sm tracking-wide" style="color: var(--text-primary)">SVG</span>
                <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-600 dark:text-blue-400">Vector</span>
              </div>
              <p class="text-xs font-mono mt-1.5" style="color: var(--text-secondary)">image/svg+xml</p>
            </div>
            <div
              class="p-3 rounded-lg border transition-colors shadow-sm"
              style="background-color: var(--bg-card); border-color: var(--border)"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-sm tracking-wide" style="color: var(--text-primary)">PDF</span>
                <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400">Document</span>
              </div>
              <p class="text-xs font-mono mt-1.5" style="color: var(--text-secondary)">application/pdf</p>
            </div>
            <div
              class="p-3 rounded-lg border transition-colors shadow-sm"
              style="background-color: var(--bg-card); border-color: var(--border)"
            >
              <div class="flex items-center justify-between">
                <span class="font-bold text-sm tracking-wide" style="color: var(--text-primary)">EPS</span>
                <span class="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-600 dark:text-amber-400">Vector</span>
              </div>
              <p class="text-xs font-mono mt-1.5" style="color: var(--text-secondary)">application/postscript</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── Section 7: Async Batch Export ────────────────────────── -->
    <section class="space-y-4">
      <div class="flex items-center gap-3">
        <span class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500/10 text-primary-500 font-bold text-sm">7</span>
        <div>
          <h2 class="text-xl font-bold text-surface-900 dark:text-surface-0">Asynchronous Export (Background Queue)</h2>
          <p class="text-xs text-surface-500">
            For high-volume automation or bulk printing, dispatch tasks to the Celery export worker
          </p>
        </div>
      </div>

      <div
        class="rounded-xl border p-5 space-y-4"
        style="background-color: var(--bg-card); border-color: var(--border)"
      >
        <p class="text-sm text-surface-700 dark:text-surface-300 leading-relaxed">
          If you have automated pipelines or large batch workloads, enqueue the generation task via
          <code class="px-1.5 py-0.5 rounded text-xs font-mono" style="background: var(--bg-elevated)">POST /api/v1/qrcodes/{id}/export/async?format=png</code>.
          This returns a <strong>202 Accepted</strong> with a job object. You can then poll
          <code class="px-1.5 py-0.5 rounded text-xs font-mono" style="background: var(--bg-elevated)">GET /api/v1/qrcodes/jobs/{job_id}</code>
          to retrieve the permanent static download URL once status reaches <code>COMPLETED</code>.
        </p>

        <div
          class="rounded-xl border overflow-hidden shadow-sm"
          style="background-color: var(--bg-card); border-color: var(--border)"
        >
          <div
            class="flex items-center justify-between px-4 py-3 border-b text-xs font-mono"
            style="background-color: var(--bg-elevated); border-color: var(--border)"
          >
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded font-bold bg-amber-500/20 text-amber-600 dark:text-amber-400">202 ACCEPTED</span>
              <span class="text-surface-700 dark:text-surface-300">/api/v1/qrcodes/{id}/export/async</span>
            </div>
            <button
              @click="copyText('async-code', asyncExportSnippet)"
              class="flex items-center gap-1 px-2.5 py-1 rounded border hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
              style="border-color: var(--border)"
            >
              <i :class="copiedSnippets['async-code'] ? 'pi pi-check text-emerald-500' : 'pi pi-copy text-surface-400'" />
              <span class="font-sans">{{ copiedSnippets['async-code'] ? 'Copied' : 'Copy' }}</span>
            </button>
          </div>

          <pre
            class="p-4 text-xs font-mono overflow-x-auto leading-relaxed"
            style="background-color: var(--bg-card); color: var(--text-primary); white-space: pre;"
          ><code># 1. Enqueue background export job
curl -X POST "{{ apiBaseUrl }}/qrcodes/{id}/export/async?format=png" \
  -H "X-API-Key: pqr_your_key_here"

# Sample 202 Response:
# {
#   "id": "7bfa8812-42da-4b36-a192-d9f7831d102e",
#   "status": "PENDING",
#   "total_items": 1,
#   "processed_items": 0,
#   "result_url": null
# }

# 2. Poll job status until COMPLETED
curl -X GET "{{ apiBaseUrl }}/qrcodes/jobs/{job_id}" \
  -H "X-API-Key: pqr_your_key_here"

# Sample Completed Response:
# {
#   "id": "7bfa8812-42da-4b36-a192-d9f7831d102e",
#   "status": "COMPLETED",
#   "total_items": 1,
#   "processed_items": 1,
#   "result_url": "/static/exports/7bfa8812-42da-4b36-a192-d9f7831d102e.png"
# }</code></pre>
        </div>
      </div>
    </section>

    <!-- ── Interactive API Explorer Banner ──────────────────────── -->
    <div
      class="rounded-2xl border p-6 flex flex-col sm:flex-row items-center justify-between gap-6"
      style="background: linear-gradient(135deg, var(--color-primary-soft) 0%, var(--bg-elevated) 100%); border-color: var(--border)"
    >
      <div class="space-y-1">
        <h3 class="text-lg font-bold text-surface-900 dark:text-surface-0 flex items-center gap-2">
          <i class="pi pi-book text-primary-500" />
          <span>Complete OpenAPI / ReDoc Specification</span>
        </h3>
        <p class="text-sm text-surface-600 dark:text-surface-400 max-w-xl">
          Want to explore request schemas, full error responses, scan analytics endpoints, and try live requests directly in your browser?
        </p>
      </div>
      <div class="flex items-center gap-3">
        <a
          :href="redocUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="px-5 py-2.5 rounded-xl font-bold text-sm text-white shadow transition-transform hover:-translate-y-0.5 whitespace-nowrap"
          style="background-color: var(--color-primary)"
        >
          Open ReDoc &rarr;
        </a>
      </div>
    </div>

  </div>
</template>

<style scoped>
.api-docs-container pre {
  margin: 0;
}
</style>

