<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class StagedFact extends Model
{
    protected $table = 'staged_facts';

    protected $guarded = [];

    protected $casts = [
        'confidence' => 'float',
    ];
}
