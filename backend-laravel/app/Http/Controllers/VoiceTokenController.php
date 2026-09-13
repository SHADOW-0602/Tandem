<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Firebase\JWT\JWT;

class VoiceTokenController extends Controller
{
    public function mint(Request $request)
    {
        $vertical = $request->input('vertical', 'dispatch');
        $roomName = $request->input('room_name') ?: 'tandem-room-' . substr(bin2hex(random_bytes(6)), 0, 10);
        $identity = 'caller-' . substr(bin2hex(random_bytes(4)), 0, 8);

        $apiKey = env('LIVEKIT_API_KEY', 'APIxQ7iGjF7ZfD2');
        $apiSecret = env('LIVEKIT_API_SECRET', 'SECUQo3i3h8Wf4P3k2L7m1N9q5R8t2V4x6Z8b0d2');
        $livekitUrl = env('LIVEKIT_URL', 'wss://parity-9hhf288x.livekit.cloud');

        $now = time();
        $payload = [
            'iss' => $apiKey,
            'sub' => $identity,
            'nbf' => $now,
            'exp' => $now + 3600 * 2, // 2 hour valid session
            'video' => [
                'room' => $roomName,
                'roomJoin' => true,
                'canPublish' => true,
                'canSubscribe' => true,
            ],
            'metadata' => json_encode([
                'vertical' => $vertical,
            ]),
        ];

        $token = JWT::encode($payload, $apiSecret, 'HS256');

        return response()->json([
            'token' => $token,
            'url' => $livekitUrl,
            'room_name' => $roomName,
            'identity' => $identity,
            'vertical' => $vertical,
        ]);
    }
}
