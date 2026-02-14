import datetime
import hashlib
import hmac
import json
import os
import time
import uuid
import zlib
from typing import Dict, List, Optional

import requests


ENGINE_QWEN3_LOCAL = "qwen3_local"
ENGINE_BCUT = "bcut"
ENGINE_JIANYING = "jianying"
ENGINE_KUAISHOU = "kuaishou"

ASR_ENGINE_DEFINITIONS = [
    {
        "id": ENGINE_QWEN3_LOCAL,
        "label": "Qwen3本地模型",
        "description": "使用本地 Qwen3-ASR 模型离线推理。",
        "kind": "local",
    },
    {
        "id": ENGINE_BCUT,
        "label": "BCut接口",
        "description": "AsrTools 同源在线识别接口。",
        "kind": "online",
    },
    {
        "id": ENGINE_JIANYING,
        "label": "JianYing接口",
        "description": "AsrTools 同源在线识别接口。",
        "kind": "online",
    },
    {
        "id": ENGINE_KUAISHOU,
        "label": "KuaiShou接口",
        "description": "AsrTools 同源在线识别接口。",
        "kind": "online",
    },
]

_ENGINE_IDS = {item["id"] for item in ASR_ENGINE_DEFINITIONS}
_ENGINE_ALIASES = {
    "qwen": ENGINE_QWEN3_LOCAL,
    "qwen3": ENGINE_QWEN3_LOCAL,
    "qwen3_local": ENGINE_QWEN3_LOCAL,
    "b": ENGINE_BCUT,
    "bcut": ENGINE_BCUT,
    "jianying": ENGINE_JIANYING,
    "j": ENGINE_JIANYING,
    "kuaishou": ENGINE_KUAISHOU,
    "k": ENGINE_KUAISHOU,
}


class AsrEngineError(RuntimeError):
    pass


def list_asr_engines(default_engine: str = ENGINE_BCUT) -> Dict[str, object]:
    try:
        resolved_default = resolve_asr_engine(default_engine, fallback=ENGINE_BCUT)
    except AsrEngineError:
        resolved_default = ENGINE_BCUT
    return {"default_engine": resolved_default, "engines": ASR_ENGINE_DEFINITIONS}


def resolve_asr_engine(engine: Optional[str], fallback: str = ENGINE_BCUT) -> str:
    candidate = str(engine or "").strip().lower()
    if not candidate:
        candidate = str(fallback or ENGINE_BCUT).strip().lower()
    if candidate in _ENGINE_IDS:
        return candidate
    if candidate in _ENGINE_ALIASES:
        return _ENGINE_ALIASES[candidate]
    available = ", ".join(sorted(_ENGINE_IDS))
    raise AsrEngineError(f"Unsupported asr_engine '{engine}'. Available: {available}")


def is_local_qwen_engine(engine: str) -> bool:
    return resolve_asr_engine(engine) == ENGINE_QWEN3_LOCAL


def transcribe_with_online_engine(
    audio_path: str,
    engine: str,
    language: Optional[str] = None,
    timeout_seconds: int = 60,
) -> Dict[str, object]:
    resolved_engine = resolve_asr_engine(engine)
    if resolved_engine == ENGINE_BCUT:
        segments = _BcutASR(audio_path, timeout_seconds=timeout_seconds).run()
    elif resolved_engine == ENGINE_JIANYING:
        segments = _JianYingASR(audio_path, timeout_seconds=timeout_seconds).run()
    elif resolved_engine == ENGINE_KUAISHOU:
        segments = _KuaiShouASR(audio_path, timeout_seconds=timeout_seconds).run()
    else:
        raise AsrEngineError(f"Online engine is not implemented: {resolved_engine}")

    text = " ".join(seg["text"].strip() for seg in segments if seg["text"].strip()).strip()
    return {"text": text, "language": language, "segments": segments}


def _read_audio_bytes(audio_path: str) -> bytes:
    if not os.path.exists(audio_path):
        raise AsrEngineError(f"Audio file not found: {audio_path}")
    with open(audio_path, "rb") as handle:
        return handle.read()


def _to_milliseconds(value) -> int:
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return 0


def _ms_to_seconds(value) -> float:
    return max(0.0, _to_milliseconds(value) / 1000.0)


def _normalize_segment(text: str, start_ms, end_ms) -> Dict[str, object]:
    start_seconds = _ms_to_seconds(start_ms)
    end_seconds = max(start_seconds, _ms_to_seconds(end_ms))
    return {
        "start": start_seconds,
        "end": end_seconds,
        "text": str(text or "").strip(),
    }


def _safe_json(response: requests.Response, context: str) -> Dict[str, object]:
    try:
        payload = response.json()
    except ValueError as exc:
        snippet = (response.text or "")[:300]
        raise AsrEngineError(f"{context}: invalid JSON response: {snippet}") from exc
    if not isinstance(payload, dict):
        raise AsrEngineError(f"{context}: unexpected JSON payload type")
    return payload


class _BcutASR:
    API_BASE_URL = "https://member.bilibili.com/x/bcut/rubick-interface"
    API_REQ_UPLOAD = API_BASE_URL + "/resource/create"
    API_COMMIT_UPLOAD = API_BASE_URL + "/resource/create/complete"
    API_CREATE_TASK = API_BASE_URL + "/task"
    API_QUERY_RESULT = API_BASE_URL + "/task/result"
    HEADERS = {
        "User-Agent": "Bilibili/1.0.0 (https://www.bilibili.com)",
        "Content-Type": "application/json",
    }

    def __init__(self, audio_path: str, timeout_seconds: int = 60):
        self.audio_path = audio_path
        self.audio_bytes = _read_audio_bytes(audio_path)
        self.timeout = timeout_seconds

    def run(self) -> List[Dict[str, object]]:
        request_payload = {
            "type": 2,
            "name": "audio.mp3",
            "size": len(self.audio_bytes),
            "ResourceFileType": "mp3",
            "model_id": "8",
        }
        response = requests.post(
            self.API_REQ_UPLOAD,
            data=json.dumps(request_payload),
            headers=self.HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()
        upload_data = _safe_json(response, "BCut apply upload").get("data") or {}

        upload_urls = upload_data.get("upload_urls") or []
        per_size = int(upload_data.get("per_size") or 0)
        if not upload_urls or per_size <= 0:
            raise AsrEngineError("BCut apply upload returned empty upload_urls/per_size")

        etags = []
        for index, upload_url in enumerate(upload_urls):
            start_pos = index * per_size
            end_pos = min(len(self.audio_bytes), (index + 1) * per_size)
            part_response = requests.put(
                upload_url,
                data=self.audio_bytes[start_pos:end_pos],
                headers=self.HEADERS,
                timeout=self.timeout,
            )
            part_response.raise_for_status()
            etags.append(part_response.headers.get("Etag", ""))

        commit_payload = {
            "InBossKey": upload_data.get("in_boss_key"),
            "ResourceId": upload_data.get("resource_id"),
            "Etags": ",".join(etags),
            "UploadId": upload_data.get("upload_id"),
            "model_id": "8",
        }
        commit_response = requests.post(
            self.API_COMMIT_UPLOAD,
            data=json.dumps(commit_payload),
            headers=self.HEADERS,
            timeout=self.timeout,
        )
        commit_response.raise_for_status()
        commit_data = _safe_json(commit_response, "BCut commit upload").get("data") or {}
        download_url = commit_data.get("download_url")
        if not download_url:
            raise AsrEngineError("BCut commit upload missing download_url")

        create_response = requests.post(
            self.API_CREATE_TASK,
            json={"resource": download_url, "model_id": "8"},
            headers=self.HEADERS,
            timeout=self.timeout,
        )
        create_response.raise_for_status()
        create_data = _safe_json(create_response, "BCut create task").get("data") or {}
        task_id = create_data.get("task_id")
        if not task_id:
            raise AsrEngineError("BCut create task missing task_id")

        task_payload = {}
        for _ in range(300):
            poll_response = requests.get(
                self.API_QUERY_RESULT,
                params={"model_id": 7, "task_id": task_id},
                headers=self.HEADERS,
                timeout=self.timeout,
            )
            poll_response.raise_for_status()
            task_payload = _safe_json(poll_response, "BCut query result").get("data") or {}
            if int(task_payload.get("state") or 0) == 4:
                break
            time.sleep(1)
        else:
            raise AsrEngineError("BCut task timeout")

        raw_result = task_payload.get("result")
        if isinstance(raw_result, str):
            raw_result = json.loads(raw_result)
        if not isinstance(raw_result, dict):
            raise AsrEngineError("BCut task result format is invalid")

        segments = []
        for utterance in raw_result.get("utterances") or []:
            segments.append(
                _normalize_segment(
                    utterance.get("transcript", ""),
                    utterance.get("start_time"),
                    utterance.get("end_time"),
                )
            )
        return [seg for seg in segments if seg["text"]]


class _KuaiShouASR:
    API_URL = "https://ai.kuaishou.com/api/effects/subtitle_generate"

    def __init__(self, audio_path: str, timeout_seconds: int = 60):
        self.audio_path = audio_path
        self.audio_bytes = _read_audio_bytes(audio_path)
        self.timeout = timeout_seconds

    def run(self) -> List[Dict[str, object]]:
        payload = {"typeId": "1"}
        files = [("file", ("audio.mp3", self.audio_bytes, "audio/mpeg"))]
        response = requests.post(
            self.API_URL,
            data=payload,
            files=files,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = _safe_json(response, "KuaiShou submit")
        data = result.get("data") or {}
        utterances = data.get("text") or []
        segments = []
        for utterance in utterances:
            segments.append(
                _normalize_segment(
                    utterance.get("text", ""),
                    utterance.get("start_time"),
                    utterance.get("end_time"),
                )
            )
        return [seg for seg in segments if seg["text"]]


class _JianYingASR:
    SIGN_ENDPOINT = "https://asrtools-update.bkfeng.top/sign"
    API_HOST = "https://lv-pc-api-sinfonlinec.ulikecam.com"

    def __init__(self, audio_path: str, timeout_seconds: int = 60):
        self.audio_path = audio_path
        self.audio_bytes = _read_audio_bytes(audio_path)
        self.file_size = len(self.audio_bytes)
        self.timeout = timeout_seconds
        self.crc32_hex = format(zlib.crc32(self.audio_bytes) & 0xFFFFFFFF, "08x")
        self.tdid = f"{uuid.getnode():012d}" if datetime.datetime.now().year == 2024 else "3943278516897751"

        self.session_token = ""
        self.secret_key = ""
        self.access_key = ""
        self.store_uri = ""
        self.auth = ""
        self.upload_id = ""
        self.upload_host = ""

    def run(self) -> List[Dict[str, object]]:
        self._upload()
        query_id = self._submit()
        response_data = {}
        for _ in range(240):
            response_data = self._query(query_id)
            utterances = ((response_data.get("data") or {}).get("utterances")) or []
            if utterances:
                break
            status = str((response_data.get("data") or {}).get("status", "")).lower()
            if status in {"failed", "error", "3"}:
                raise AsrEngineError(f"JianYing task failed: {response_data}")
            time.sleep(1)
        else:
            raise AsrEngineError("JianYing task timeout")

        utterances = ((response_data.get("data") or {}).get("utterances")) or []
        segments = []
        for utterance in utterances:
            segments.append(
                _normalize_segment(
                    utterance.get("text", ""),
                    utterance.get("start_time"),
                    utterance.get("end_time"),
                )
            )
        return [seg for seg in segments if seg["text"]]

    def _upload(self) -> None:
        self._upload_sign()
        self._upload_auth()
        self._upload_file()
        self._upload_check()
        self._upload_commit()

    def _submit(self) -> str:
        url = self.API_HOST + "/lv/v1/audio_subtitle/submit"
        payload = {
            "adjust_endtime": 200,
            "audio": self.store_uri,
            "caption_type": 2,
            "client_request_id": str(uuid.uuid4()),
            "max_lines": 1,
            "songs_info": [{"end_time": 6000, "id": "", "start_time": 0}],
            "words_per_line": 16,
        }
        sign_value, device_time = self._generate_sign_parameters("/lv/v1/audio_subtitle/submit")
        headers = self._build_headers(device_time, sign_value)
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = _safe_json(response, "JianYing submit").get("data") or {}
        query_id = data.get("id")
        if not query_id:
            raise AsrEngineError("JianYing submit missing query id")
        return query_id

    def _query(self, query_id: str) -> Dict[str, object]:
        url = self.API_HOST + "/lv/v1/audio_subtitle/query"
        payload = {"id": query_id, "pack_options": {"need_attribute": True}}
        sign_value, device_time = self._generate_sign_parameters("/lv/v1/audio_subtitle/query")
        headers = self._build_headers(device_time, sign_value)
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return _safe_json(response, "JianYing query")

    def _generate_sign_parameters(
        self,
        url_path: str,
        pf: str = "4",
        appvr: str = "4.0.0",
    ) -> tuple[str, str]:
        current_time = str(int(time.time()))
        payload = {
            "url": url_path,
            "current_time": current_time,
            "pf": pf,
            "appvr": appvr,
            "tdid": self.tdid,
        }
        response = requests.post(self.SIGN_ENDPOINT, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = _safe_json(response, "JianYing sign")
        sign_value = (data.get("sign") or "").lower()
        if not sign_value:
            raise AsrEngineError("JianYing sign endpoint returned empty sign")
        return sign_value, current_time

    def _build_headers(self, device_time: str, sign_value: str) -> Dict[str, str]:
        return {
            "User-Agent": "Cronet/TTNetVersion:01594da2 2023-03-14 QuicVersion:46688bb4 2022-11-28",
            "appvr": "4.0.0",
            "device-time": str(device_time),
            "pf": "4",
            "sign": sign_value,
            "sign-ver": "1",
            "tdid": self.tdid,
        }

    def _upload_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 Thea/1.0.1"
            ),
            "Authorization": self.auth,
            "Content-CRC32": self.crc32_hex,
        }

    def _upload_sign(self) -> None:
        url = self.API_HOST + "/lv/v1/upload_sign"
        sign_value, device_time = self._generate_sign_parameters("/lv/v1/upload_sign")
        headers = self._build_headers(device_time, sign_value)
        response = requests.post(
            url,
            data=json.dumps({"biz": "pc-recognition"}),
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = (_safe_json(response, "JianYing upload_sign").get("data")) or {}
        self.access_key = str(data.get("access_key_id") or "")
        self.secret_key = str(data.get("secret_access_key") or "")
        self.session_token = str(data.get("session_token") or "")
        if not (self.access_key and self.secret_key and self.session_token):
            raise AsrEngineError("JianYing upload_sign missing credentials")

    def _upload_auth(self) -> None:
        params = (
            "Action=ApplyUploadInner"
            f"&FileSize={self.file_size}"
            "&FileType=object"
            "&IsInner=1"
            "&SpaceName=lv-mac-recognition"
            "&Version=2020-11-19"
            "&s=5y0udbjapi"
        )
        t = datetime.datetime.utcnow()
        amz_date = t.strftime("%Y%m%dT%H%M%SZ")
        datestamp = t.strftime("%Y%m%d")
        headers = {
            "x-amz-date": amz_date,
            "x-amz-security-token": self.session_token,
        }
        signature = _aws_signature(self.secret_key, params, headers, region="cn", service="vod")
        authorization = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.access_key}/{datestamp}/cn/vod/aws4_request, "
            "SignedHeaders=x-amz-date;x-amz-security-token, "
            f"Signature={signature}"
        )
        headers["authorization"] = authorization
        response = requests.get(
            f"https://vod.bytedanceapi.com/?{params}",
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        result = _safe_json(response, "JianYing upload auth").get("Result") or {}
        upload_address = result.get("UploadAddress") or {}
        store_infos = upload_address.get("StoreInfos") or []
        upload_hosts = upload_address.get("UploadHosts") or []
        if not store_infos or not upload_hosts:
            raise AsrEngineError("JianYing upload auth missing upload hosts/store infos")
        store_info = store_infos[0]
        self.store_uri = str(store_info.get("StoreUri") or "")
        self.auth = str(store_info.get("Auth") or "")
        self.upload_id = str(store_info.get("UploadID") or "")
        self.upload_host = str(upload_hosts[0] or "")
        if not (self.store_uri and self.auth and self.upload_id and self.upload_host):
            raise AsrEngineError("JianYing upload auth fields are incomplete")

    def _upload_file(self) -> None:
        url = f"https://{self.upload_host}/{self.store_uri}?partNumber=1&uploadID={self.upload_id}"
        headers = self._upload_headers()
        response = requests.put(url, data=self.audio_bytes, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        payload = _safe_json(response, "JianYing upload file")
        if int(payload.get("success") or 1) != 0:
            raise AsrEngineError(f"JianYing upload file failed: {payload}")

    def _upload_check(self) -> None:
        url = f"https://{self.upload_host}/{self.store_uri}?uploadID={self.upload_id}"
        headers = self._upload_headers()
        response = requests.post(
            url,
            data=f"1:{self.crc32_hex}",
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        _safe_json(response, "JianYing upload check")

    def _upload_commit(self) -> None:
        url = (
            f"https://{self.upload_host}/{self.store_uri}"
            f"?uploadID={self.upload_id}&partNumber=1&x-amz-security-token={self.session_token}"
        )
        headers = self._upload_headers()
        response = requests.put(url, data=self.audio_bytes, headers=headers, timeout=self.timeout)
        response.raise_for_status()


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _signature_key(secret_key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region_name)
    k_service = _sign(k_region, service_name)
    return _sign(k_service, "aws4_request")


def _aws_signature(
    secret_key: str,
    request_parameters: str,
    headers: Dict[str, str],
    method: str = "GET",
    payload: str = "",
    region: str = "cn",
    service: str = "vod",
) -> str:
    canonical_uri = "/"
    canonical_querystring = request_parameters
    canonical_headers = "\n".join(f"{key}:{value}" for key, value in headers.items()) + "\n"
    signed_headers = ";".join(headers.keys())
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    canonical_request = (
        f"{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n"
        f"{signed_headers}\n{payload_hash}"
    )

    amz_date = headers["x-amz-date"]
    datestamp = amz_date.split("T")[0]
    credential_scope = f"{datestamp}/{region}/{service}/aws4_request"
    string_to_sign = (
        "AWS4-HMAC-SHA256\n"
        f"{amz_date}\n"
        f"{credential_scope}\n"
        f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    )
    signing_key = _signature_key(secret_key, datestamp, region, service)
    return hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
