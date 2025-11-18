// FILE: backend/routes/addManualEvent.js
const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_ANON_KEY);

module.exports = async (req, res) => {
    const { type, value1, value2, value3, valueBool, valueText } = req.body;

    if (!type) {
        return res.status(400).json({ error: 'Event type is required.' });
    }

    const insertData = {
        type: type,
        value_1: value1 ? parseInt(value1, 10) : null,
        value_2: value2 ? parseInt(value2, 10) : null,
        value_3: value3 ? parseInt(value3, 10) : null,
        value_bool: valueBool,
        value_text: valueText
    };

    try {
        const { data, error } = await supabase
            .from('health_events')
            .insert([insertData])
            .select();

        if (error) {
            throw error;
        }

        res.json({ success: true, data: data[0] });
    } catch (error) {
        console.error('Supabase manual insert error:', error);
        res.status(500).json({ error: 'Failed to save manual event.', details: error.message });
    }
};