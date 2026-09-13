<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\VoiceTokenController;
use App\Http\Controllers\VerticalController;
use App\Http\Controllers\KnowledgeController;
use App\Http\Controllers\TelemetryController;

// Health check
Route::get('/health', function () {
    return response()->json([
        'status' => 'healthy',
        'backend' => 'Laravel 11',
        'php_version' => PHP_VERSION,
        'database' => config('database.default'),
        'timestamp' => time(),
    ]);
});

// LiveKit WebRTC token minting with character persona metadata
Route::post('/token', [VoiceTokenController::class, 'mint']);

// Vertical & Character Persona metadata
Route::get('/verticals', [VerticalController::class, 'index']);
Route::get('/verticals/{id}', [VerticalController::class, 'show']);

// Knowledge & Staging routes
Route::get('/knowledge/staging', [KnowledgeController::class, 'staging']);
Route::post('/knowledge/staging/{stageId}/approve', [KnowledgeController::class, 'approve']);
Route::post('/knowledge/staging/{stageId}/reject', [KnowledgeController::class, 'reject']);
Route::post('/knowledge/search', [KnowledgeController::class, 'search']);
Route::get('/knowledge/{verticalId}', [KnowledgeController::class, 'show']);

// Telemetry & Latency analytics
Route::post('/telemetry', [TelemetryController::class, 'store']);
Route::get('/telemetry/stats', [TelemetryController::class, 'stats']);
