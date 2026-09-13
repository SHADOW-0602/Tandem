<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('staged_facts', function (Blueprint $table) {
            $table->id();
            $table->string('stage_id')->unique();
            $table->string('vertical')->index();
            $table->string('doc_id');
            $table->string('field_key');
            $table->text('old_value')->nullable();
            $table->text('new_value');
            $table->text('verbatim_quote');
            $table->float('confidence')->default(0.9);
            $table->string('status')->default('pending'); // pending, approved, rejected
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('staged_facts');
    }
};
