<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('telemetries', function (Blueprint $table) {
            $table->id();
            $table->string('call_id')->index();
            $table->integer('turn_id')->default(1);
            $table->string('vertical')->index();
            $table->text('user_transcript');
            $table->text('agent_response');
            $table->json('retrieved_doc_ids')->nullable();
            $table->json('retrieved_snippets')->nullable();
            $table->string('guardrail_action')->nullable();
            $table->float('stt_latency_ms')->default(0);
            $table->float('moss_latency_ms')->default(0);
            $table->float('llm_ttft_ms')->default(0);
            $table->float('tts_ttfb_ms')->default(0);
            $table->float('total_latency_ms')->default(0);
            $table->boolean('is_sub_10ms_moss')->default(true);
            $table->boolean('within_budget')->default(true);
            $table->bigInteger('timestamp')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('telemetries');
    }
};
