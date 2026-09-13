<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Telemetry extends Model
{
    protected $table = 'telemetries';

    protected $guarded = [];

    protected $casts = [
        'retrieved_doc_ids' => 'array',
        'retrieved_snippets' => 'array',
        'is_sub_10ms_moss' => 'boolean',
        'within_budget' => 'boolean',
        'stt_latency_ms' => 'float',
        'moss_latency_ms' => 'float',
        'llm_ttft_ms' => 'float',
        'tts_ttfb_ms' => 'float',
        'total_latency_ms' => 'float',
    ];
}
