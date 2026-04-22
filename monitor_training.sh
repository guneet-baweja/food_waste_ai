#!/bin/zsh

# 📊 Monitor training progress in real-time

echo "🔍 Monitoring Training Progress..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    clear
    echo "⏰ Last Update: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Show checkpoint file info
    if [ -f "ai/models/efficientnet_best.pth" ]; then
        MODIFIED=$(stat -f %Sm -t "%Y-%m-%d %H:%M:%S" ai/models/efficientnet_best.pth)
        SIZE=$(ls -lh ai/models/efficientnet_best.pth | awk '{print $5}')
        echo "📦 Checkpoint: $SIZE (Updated: $MODIFIED)"
    fi
    
    # Show resume results if available
    if [ -f "ai/models/resume_results.json" ]; then
        echo ""
        echo "📊 Latest Results:"
        cat ai/models/resume_results.json | grep -E "best_accuracy|final_epoch|total_time" | sed 's/^/  /'
    fi
    
    echo ""
    echo "✨ Training is running in background..."
    echo "   Terminal ID: 092be62f-25e0-472e-9a29-85a6610d6f72"
    echo ""
    echo "📝 View full output with:"
    echo "   tail -f /tmp/training.log"
    
    sleep 5
done
