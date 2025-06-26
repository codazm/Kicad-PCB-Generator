"""EMC analysis module for KiCad PCB layouts."""
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional, TYPE_CHECKING
import pcbnew
from enum import Enum
import numpy as np
from pathlib import Path

from ..base.base_analyzer import BaseAnalyzer
from ..base.results.analysis_result import AnalysisResult, AnalysisType, AnalysisSeverity
from ..audio.analysis.analyzer import SignalIntegrityAnalysis, EMIAnalysis
from ..audio.validation.audio_validator import AudioPCBValidator
from ..validation.safety_validator import SafetyValidator
from ..base.base_config import BaseConfig
from ..base.results.config_result import ConfigResult, ConfigStatus, ConfigFormat
from ...utils.logger import Logger

if TYPE_CHECKING:
    import pcbnew

@dataclass
class EMCAnalysisConfigItem:
    """Configuration item for EMC analysis."""
    # Signal integrity thresholds
    crosstalk_threshold: float = -40.0  # dB
    reflection_threshold: float = 0.1  # 10%
    impedance_mismatch_threshold: float = 5.0  # 5%
    signal_quality_threshold: float = 0.8  # 80%
    
    # EMI/EMC thresholds
    radiated_emissions_limit: float = 40.0  # dBμV/m
    conducted_emissions_limit: float = 30.0  # dBμV
    susceptibility_limit: float = 50.0  # dBμV/m
    compliance_margin: float = 10.0  # dB
    
    # Analysis parameters
    frequency_range: Tuple[float, float] = field(default=(10e3, 1e9))  # 10kHz to 1GHz
    frequency_points: int = 100
    temperature: float = 25.0  # °C
    
    # Stackup parameters
    dielectric_constant: float = 4.5  # FR4
    substrate_height: float = 0.035  # mm
    copper_thickness: float = 0.035  # mm
    copper_weight: float = 1.0  # oz
    prepreg_thickness: float = 0.1  # mm

class EMCAnalysisConfig(BaseConfig[EMCAnalysisConfigItem]):
    """Configuration manager for EMC analysis."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        """Initialize EMC analysis configuration.
        
        Args:
            config_data: Configuration data dictionary
        """
        super().__init__(config_data or {})
        self.logger = Logger(__name__).get_logger()
        
    def _validate_config(self, config: EMCAnalysisConfigItem) -> ConfigResult:
        """Validate EMC analysis configuration.
        
        Args:
            config: Configuration item to validate
            
        Returns:
            ConfigResult with validation status
        """
        try:
            # Validate signal integrity thresholds
            if config.crosstalk_threshold > 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Crosstalk threshold should be negative (dB)",
                    data=config
                )
            
            if config.reflection_threshold <= 0 or config.reflection_threshold > 1:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Reflection threshold must be between 0 and 1",
                    data=config
                )
            
            if config.impedance_mismatch_threshold <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Impedance mismatch threshold must be positive",
                    data=config
                )
            
            if config.signal_quality_threshold <= 0 or config.signal_quality_threshold > 1:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Signal quality threshold must be between 0 and 1",
                    data=config
                )
            
            # Validate EMI/EMC thresholds
            if config.radiated_emissions_limit <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Radiated emissions limit must be positive",
                    data=config
                )
            
            if config.conducted_emissions_limit <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Conducted emissions limit must be positive",
                    data=config
                )
            
            if config.susceptibility_limit <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Susceptibility limit must be positive",
                    data=config
                )
            
            if config.compliance_margin <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Compliance margin must be positive",
                    data=config
                )
            
            # Validate frequency range
            if config.frequency_range[0] >= config.frequency_range[1]:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Frequency range start must be less than end",
                    data=config
                )
            
            if config.frequency_range[0] <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Frequency range start must be positive",
                    data=config
                )
            
            # Validate frequency points
            if config.frequency_points <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Frequency points must be positive",
                    data=config
                )
            
            # Validate temperature
            if config.temperature < -273.15:  # Absolute zero
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Temperature cannot be below absolute zero",
                    data=config
                )
            
            # Validate stackup parameters
            if config.dielectric_constant <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Dielectric constant must be positive",
                    data=config
                )
            
            if config.substrate_height <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Substrate height must be positive",
                    data=config
                )
            
            if config.copper_thickness <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Copper thickness must be positive",
                    data=config
                )
            
            if config.copper_weight <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Copper weight must be positive",
                    data=config
                )
            
            if config.prepreg_thickness <= 0:
                return ConfigResult(
                    status=ConfigStatus.ERROR,
                    message="Prepreg thickness must be positive",
                    data=config
                )
            
            return ConfigResult(
                status=ConfigStatus.SUCCESS,
                message="EMC analysis configuration validated successfully",
                data=config
            )
            
        except Exception as e:
            self.logger.error(f"Error validating EMC analysis configuration: {e}")
            return ConfigResult(
                status=ConfigStatus.ERROR,
                message=f"Configuration validation failed: {e}",
                data=config
            )
    
    def _parse_config(self, config_data: Dict[str, Any]) -> EMCAnalysisConfigItem:
        """Parse configuration data into EMCAnalysisConfigItem.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            EMCAnalysisConfigItem instance
        """
        try:
            return EMCAnalysisConfigItem(
                crosstalk_threshold=config_data.get('crosstalk_threshold', -40.0),
                reflection_threshold=config_data.get('reflection_threshold', 0.1),
                impedance_mismatch_threshold=config_data.get('impedance_mismatch_threshold', 5.0),
                signal_quality_threshold=config_data.get('signal_quality_threshold', 0.8),
                radiated_emissions_limit=config_data.get('radiated_emissions_limit', 40.0),
                conducted_emissions_limit=config_data.get('conducted_emissions_limit', 30.0),
                susceptibility_limit=config_data.get('susceptibility_limit', 50.0),
                compliance_margin=config_data.get('compliance_margin', 10.0),
                frequency_range=tuple(config_data.get('frequency_range', [10e3, 1e9])),
                frequency_points=config_data.get('frequency_points', 100),
                temperature=config_data.get('temperature', 25.0),
                dielectric_constant=config_data.get('dielectric_constant', 4.5),
                substrate_height=config_data.get('substrate_height', 0.035),
                copper_thickness=config_data.get('copper_thickness', 0.035),
                copper_weight=config_data.get('copper_weight', 1.0),
                prepreg_thickness=config_data.get('prepreg_thickness', 0.1)
            )
        except Exception as e:
            self.logger.error(f"Error parsing EMC analysis configuration: {e}")
            raise ValueError(f"Invalid EMC analysis configuration data: {e}")
    
    def _prepare_config_data(self, config: EMCAnalysisConfigItem) -> Dict[str, Any]:
        """Prepare configuration item for serialization.
        
        Args:
            config: Configuration item to prepare
            
        Returns:
            Dictionary representation of configuration
        """
        return {
            'crosstalk_threshold': config.crosstalk_threshold,
            'reflection_threshold': config.reflection_threshold,
            'impedance_mismatch_threshold': config.impedance_mismatch_threshold,
            'signal_quality_threshold': config.signal_quality_threshold,
            'radiated_emissions_limit': config.radiated_emissions_limit,
            'conducted_emissions_limit': config.conducted_emissions_limit,
            'susceptibility_limit': config.susceptibility_limit,
            'compliance_margin': config.compliance_margin,
            'frequency_range': list(config.frequency_range),
            'frequency_points': config.frequency_points,
            'temperature': config.temperature,
            'dielectric_constant': config.dielectric_constant,
            'substrate_height': config.substrate_height,
            'copper_thickness': config.copper_thickness,
            'copper_weight': config.copper_weight,
            'prepreg_thickness': config.prepreg_thickness
        }

@dataclass
class EMCAnalysisItem:
    """Represents an EMC analysis item managed by EMCAnalyzer."""
    id: str
    analysis_type: AnalysisType
    board: Optional[Any] = None
    config: Optional[EMCAnalysisConfigItem] = None
    audio_validator: Optional[AudioPCBValidator] = None
    safety_validator: Optional[SafetyValidator] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class EMCAnalyzer(BaseAnalyzer[EMCAnalysisItem]):
    """EMC analysis manager for KiCad PCB layouts."""
    
    def __init__(self, board: "pcbnew.BOARD", config: Optional[EMCAnalysisConfigItem] = None, logger: Optional[logging.Logger] = None):
        """Initialize the EMC analyzer.
        
        Args:
            board: KiCad board object
            config: Optional configuration for EMC analysis
            logger: Optional logger instance
        """
        super().__init__("EMCAnalyzer")
        self.board = board
        self.config = config or EMCAnalysisConfigItem()
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize validators
        self.audio_validator = AudioPCBValidator()
        self.safety_validator = SafetyValidator()
        
        # Validate KiCad version
        self._validate_kicad_version()
        
        # Initialize analysis items
        self._initialize_analysis_items()
    
    def _initialize_analysis_items(self) -> None:
        """Initialize analysis items for BaseAnalyzer."""
        try:
            # Create analysis items for each analysis type
            analysis_types = [
                AnalysisType.EMI_EMC,
                AnalysisType.SIGNAL_INTEGRITY,
                AnalysisType.POWER_ANALYSIS,
                AnalysisType.CROSSTALK_ANALYSIS
            ]
            
            for analysis_type in analysis_types:
                analysis_item = EMCAnalysisItem(
                    id=f"emc_analysis_{analysis_type.value}",
                    analysis_type=analysis_type,
                    board=self.board,
                    config=self.config,
                    audio_validator=self.audio_validator,
                    safety_validator=self.safety_validator
                )
                self.create(f"emc_analysis_{analysis_type.value}", analysis_item)
                
        except Exception as e:
            self.logger.error(f"Error initializing analysis items: {str(e)}")
            raise
    
    def _validate_kicad_version(self) -> None:
        """Validate KiCad version compatibility."""
        if not hasattr(pcbnew, 'VERSION') or pcbnew.VERSION < '9.0.0':
            raise RuntimeError("EMC analysis requires KiCad 9.0 or later")
    
    def analyze_emc(self) -> Dict[str, Any]:
        """Perform comprehensive EMC analysis.
        
        Returns:
            Dict containing analysis results
        """
        try:
            # Create analysis item for comprehensive EMC analysis
            emc_item = EMCAnalysisItem(
                id="comprehensive_emc_analysis",
                analysis_type=AnalysisType.EMI_EMC,
                board=self.board,
                config=self.config,
                audio_validator=self.audio_validator,
                safety_validator=self.safety_validator
            )
            
            # Perform analysis using BaseAnalyzer
            result = self.analyze(emc_item, AnalysisType.EMI_EMC)
            
            if result.success and result.data:
                return result.data
            else:
                # Fallback to original implementation
                return self._perform_comprehensive_emc_analysis()
                
        except Exception as e:
            self.logger.error(f"Error performing EMC analysis: {str(e)}")
            return {}
    
    def analyze_signal_integrity(self) -> SignalIntegrityAnalysis:
        """Analyze signal integrity.
        
        Returns:
            SignalIntegrityAnalysis object with results
        """
        try:
            # Create analysis item for signal integrity analysis
            si_item = EMCAnalysisItem(
                id="signal_integrity_analysis_current",
                analysis_type=AnalysisType.SIGNAL_INTEGRITY,
                board=self.board,
                config=self.config,
                audio_validator=self.audio_validator,
                safety_validator=self.safety_validator
            )
            
            # Perform analysis using BaseAnalyzer
            result = self.analyze(si_item, AnalysisType.SIGNAL_INTEGRITY)
            
            if result.success and result.data:
                return result.data
            else:
                # Fallback to original implementation
                return self._perform_signal_integrity_analysis()
                
        except Exception as e:
            self.logger.error(f"Error analyzing signal integrity: {str(e)}")
            return SignalIntegrityAnalysis({}, {}, {}, {})
    
    def analyze_emi(self) -> EMIAnalysis:
        """Analyze EMI/EMC characteristics.
        
        Returns:
            EMIAnalysis object with results
        """
        try:
            # Create analysis item for EMI analysis
            emi_item = EMCAnalysisItem(
                id="emi_analysis_current",
                analysis_type=AnalysisType.EMI_EMC,
                board=self.board,
                config=self.config,
                audio_validator=self.audio_validator,
                safety_validator=self.safety_validator
            )
            
            # Perform analysis using BaseAnalyzer
            result = self.analyze(emi_item, AnalysisType.EMI_EMC)
            
            if result.success and result.data:
                return result.data
            else:
                # Fallback to original implementation
                return self._perform_emi_analysis()
                
        except Exception as e:
            self.logger.error(f"Error analyzing EMI: {str(e)}")
            return EMIAnalysis({}, {}, {}, 0.0)
    
    def validate_safety(self) -> Dict[str, Any]:
        """Validate safety requirements.
        
        Returns:
            Dict containing safety validation results
        """
        try:
            # Create analysis item for safety validation
            safety_item = EMCAnalysisItem(
                id="safety_validation_current",
                analysis_type=AnalysisType.CUSTOM,
                board=self.board,
                config=self.config,
                audio_validator=self.audio_validator,
                safety_validator=self.safety_validator
            )
            
            # Perform validation using BaseAnalyzer
            result = self.analyze(safety_item, AnalysisType.CUSTOM)
            
            if result.success and result.data:
                return result.data
            else:
                # Fallback to original implementation
                return self._perform_safety_validation()
                
        except Exception as e:
            self.logger.error(f"Error validating safety: {str(e)}")
            return {}
    
    def validate_audio(self) -> Dict[str, Any]:
        """Validate audio-specific requirements.
        
        Returns:
            Dict containing audio validation results
        """
        try:
            # Create analysis item for audio validation
            audio_item = EMCAnalysisItem(
                id="audio_validation_current",
                analysis_type=AnalysisType.CUSTOM,
                board=self.board,
                config=self.config,
                audio_validator=self.audio_validator,
                safety_validator=self.safety_validator
            )
            
            # Perform validation using BaseAnalyzer
            result = self.analyze(audio_item, AnalysisType.CUSTOM)
            
            if result.success and result.data:
                return result.data
            else:
                # Fallback to original implementation
                return self._perform_audio_validation()
                
        except Exception as e:
            self.logger.error(f"Error validating audio: {str(e)}")
            return {}
    
    def _validate_target(self, target: EMCAnalysisItem) -> AnalysisResult:
        """Validate target before analysis.
        
        Args:
            target: Target to validate
            
        Returns:
            Validation result
        """
        try:
            if not target.id:
                return AnalysisResult(
                    success=False,
                    analysis_type=target.analysis_type,
                    message="Analysis item ID is required",
                    errors=["Analysis item ID cannot be empty"]
                )
            
            if not target.board:
                return AnalysisResult(
                    success=False,
                    analysis_type=target.analysis_type,
                    message="Board object is required",
                    errors=["Board object cannot be empty"]
                )
            
            if not target.config:
                return AnalysisResult(
                    success=False,
                    analysis_type=target.analysis_type,
                    message="Configuration is required",
                    errors=["Configuration cannot be empty"]
                )
            
            return AnalysisResult(
                success=True,
                analysis_type=target.analysis_type,
                message="Analysis item validation successful"
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                analysis_type=target.analysis_type,
                message=f"Analysis item validation failed: {e}",
                errors=[str(e)]
            )
    
    def _perform_analysis(self, target: EMCAnalysisItem, analysis_type: AnalysisType) -> AnalysisResult:
        """Perform the actual analysis.
        
        Args:
            target: Target to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis result
        """
        try:
            if analysis_type == AnalysisType.EMI_EMC:
                result_data = self._perform_comprehensive_emc_analysis()
                return AnalysisResult(
                    success=True,
                    analysis_type=analysis_type,
                    message="EMC analysis completed successfully",
                    data=result_data,
                    metrics={
                        "compliance_margin": result_data.get("emi_analysis", {}).get("compliance_margin", 0)
                    }
                )
            
            elif analysis_type == AnalysisType.SIGNAL_INTEGRITY:
                result_data = self._perform_signal_integrity_analysis()
                return AnalysisResult(
                    success=True,
                    analysis_type=analysis_type,
                    message="Signal integrity analysis completed successfully",
                    data=result_data,
                    metrics={
                        "avg_signal_quality": sum(result_data.signal_quality.values()) / len(result_data.signal_quality) if result_data.signal_quality else 0
                    }
                )
            
            elif analysis_type == AnalysisType.CUSTOM:
                # Handle custom analysis types (safety, audio validation)
                if "safety" in target.id:
                    result_data = self._perform_safety_validation()
                    return AnalysisResult(
                        success=True,
                        analysis_type=analysis_type,
                        message="Safety validation completed successfully",
                        data=result_data
                    )
                elif "audio" in target.id:
                    result_data = self._perform_audio_validation()
                    return AnalysisResult(
                        success=True,
                        analysis_type=analysis_type,
                        message="Audio validation completed successfully",
                        data=result_data
                    )
                else:
                    return AnalysisResult(
                        success=False,
                        analysis_type=analysis_type,
                        message=f"Unknown custom analysis type: {target.id}",
                        errors=[f"Custom analysis type {target.id} is not supported"]
                    )
            
            else:
                return AnalysisResult(
                    success=False,
                    analysis_type=analysis_type,
                    message=f"Unsupported analysis type: {analysis_type.value}",
                    errors=[f"Analysis type {analysis_type.value} is not supported"]
                )
                
        except Exception as e:
            return AnalysisResult(
                success=False,
                analysis_type=analysis_type,
                message=f"Error during analysis: {e}",
                errors=[str(e)]
            )
    
    def _perform_comprehensive_emc_analysis(self) -> Dict[str, Any]:
        """Perform comprehensive EMC analysis.
        
        Returns:
            Dict containing analysis results
        """
        try:
            # Analyze signal integrity
            signal_integrity = self._perform_signal_integrity_analysis()
            
            # Analyze EMI/EMC
            emi_analysis = self._perform_emi_analysis()
            
            # Validate safety
            safety_results = self._perform_safety_validation()
            
            # Validate audio-specific requirements
            audio_results = self._perform_audio_validation()
            
            return {
                'signal_integrity': signal_integrity,
                'emi_analysis': emi_analysis,
                'safety_results': safety_results,
                'audio_results': audio_results
            }
            
        except Exception as e:
            self.logger.error(f"Error performing comprehensive EMC analysis: {str(e)}")
            return {}
    
    def _perform_signal_integrity_analysis(self) -> SignalIntegrityAnalysis:
        """Analyze signal integrity.
        
        Returns:
            SignalIntegrityAnalysis object with results
        """
        try:
            # Get all tracks
            tracks = self.board.GetTracks()
            
            # Initialize results
            crosstalk = {}
            reflections = {}
            impedance_mismatch = {}
            signal_quality = {}
            
            # Analyze each track
            for track in tracks:
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                net_name = track.GetNetname()
                
                # Calculate crosstalk
                crosstalk[net_name] = self._calculate_crosstalk(track)
                
                # Calculate reflections
                reflections[net_name] = self._calculate_reflections(track)
                
                # Calculate impedance mismatch
                impedance_mismatch[net_name] = self._calculate_impedance_mismatch(track)
                
                # Calculate signal quality
                signal_quality[net_name] = self._calculate_signal_quality(
                    crosstalk[net_name],
                    reflections[net_name],
                    impedance_mismatch[net_name]
                )
            
            return SignalIntegrityAnalysis(
                crosstalk=crosstalk,
                reflections=reflections,
                impedance_mismatch=impedance_mismatch,
                signal_quality=signal_quality
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing signal integrity: {str(e)}")
            return SignalIntegrityAnalysis({}, {}, {}, {})
    
    def _perform_emi_analysis(self) -> EMIAnalysis:
        """Analyze EMI/EMC characteristics.
        
        Returns:
            EMIAnalysis object with results
        """
        try:
            # Generate frequency points
            f_min, f_max = self.config.frequency_range
            frequencies = [f_min * (f_max/f_min)**(i/(self.config.frequency_points-1))
                         for i in range(self.config.frequency_points)]
            
            # Initialize results
            radiated_emissions = {}
            conducted_emissions = {}
            susceptibility = {}
            
            # Analyze at each frequency
            for freq in frequencies:
                # Calculate radiated emissions
                radiated_emissions[freq] = self._calculate_radiated_emissions(freq)
                
                # Calculate conducted emissions
                conducted_emissions[freq] = self._calculate_conducted_emissions(freq)
                
                # Calculate susceptibility
                susceptibility[freq] = self._calculate_susceptibility(freq)
            
            # Calculate compliance margin
            compliance_margin = self._calculate_compliance_margin(
                radiated_emissions,
                conducted_emissions
            )
            
            return EMIAnalysis(
                radiated_emissions=radiated_emissions,
                conducted_emissions=conducted_emissions,
                susceptibility=susceptibility,
                compliance_margin=compliance_margin
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing EMI: {str(e)}")
            return EMIAnalysis({}, {}, {}, 0.0)
    
    def _perform_safety_validation(self) -> Dict[str, Any]:
        """Validate safety requirements.
        
        Returns:
            Dict containing safety validation results
        """
        try:
            # Perform safety validation using the safety validator
            safety_results = self.safety_validator.validate_board(self.board)
            
            return {
                'safety_compliance': safety_results.get('compliance', False),
                'safety_issues': safety_results.get('issues', []),
                'safety_score': safety_results.get('score', 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating safety: {str(e)}")
            return {
                'safety_compliance': False,
                'safety_issues': [f"Safety validation error: {str(e)}"],
                'safety_score': 0.0
            }
    
    def _perform_audio_validation(self) -> Dict[str, Any]:
        """Validate audio-specific requirements.
        
        Returns:
            Dict containing audio validation results
        """
        try:
            # Perform audio validation using the audio validator
            audio_results = self.audio_validator.validate_board(self.board)
            
            return {
                'audio_compliance': audio_results.get('compliance', False),
                'audio_issues': audio_results.get('issues', []),
                'audio_score': audio_results.get('score', 0.0)
            }
            
        except Exception as e:
            self.logger.error(f"Error validating audio: {str(e)}")
            return {
                'audio_compliance': False,
                'audio_issues': [f"Audio validation error: {str(e)}"],
                'audio_score': 0.0
            }
    
    def _calculate_crosstalk(self, track: pcbnew.TRACK) -> float:
        """Calculate crosstalk for a track.
        
        Args:
            track: KiCad track object
            
        Returns:
            float: Crosstalk level in dB
        """
        try:
            # Get track properties
            width = track.GetWidth() / 1e6  # Convert nm to mm
            length = track.GetLength() / 1e6  # Convert nm to mm
            
            # Get nearby tracks
            nearby_tracks = self._get_nearby_tracks(track)
            
            # Calculate crosstalk using simplified model
            total_crosstalk = 0.0
            for nearby_track in nearby_tracks:
                distance = self._calculate_min_distance(track, nearby_track)
                if distance > 0:
                    # Simplified crosstalk calculation
                    k = 0.01  # Crosstalk coefficient
                    crosstalk = k * length / distance
                    total_crosstalk += crosstalk
            
            # Convert to dB
            return 20 * math.log10(total_crosstalk) if total_crosstalk > 0 else -100.0
            
        except Exception as e:
            self.logger.error(f"Error calculating crosstalk: {str(e)}")
            return -100.0
    
    def _calculate_reflections(self, track: pcbnew.TRACK) -> float:
        """Calculate reflections for a track.
        
        Args:
            track: KiCad track object
            
        Returns:
            float: Reflection coefficient
        """
        try:
            # Calculate characteristic impedance
            z0 = self._calculate_impedance(track)
            
            # Assume load impedance (simplified)
            zl = 50.0  # ohms
            
            # Calculate reflection coefficient
            reflection_coeff = abs((zl - z0) / (zl + z0))
            
            return reflection_coeff
            
        except Exception as e:
            self.logger.error(f"Error calculating reflections: {str(e)}")
            return 0.1
    
    def _calculate_impedance_mismatch(self, track: pcbnew.TRACK) -> float:
        """Calculate impedance mismatch for a track.
        
        Args:
            track: KiCad track object
            
        Returns:
            float: Impedance mismatch percentage
        """
        try:
            # Calculate characteristic impedance
            z0 = self._calculate_impedance(track)
            
            # Assume target impedance
            z_target = 50.0  # ohms
            
            # Calculate mismatch percentage
            mismatch = abs(z0 - z_target) / z_target * 100
            
            return mismatch
            
        except Exception as e:
            self.logger.error(f"Error calculating impedance mismatch: {str(e)}")
            return 5.0
    
    def _calculate_signal_quality(self, crosstalk: float, reflections: float, impedance_mismatch: float) -> float:
        """Calculate signal quality score.
        
        Args:
            crosstalk: Crosstalk level in dB
            reflections: Reflection coefficient
            impedance_mismatch: Impedance mismatch percentage
            
        Returns:
            float: Signal quality score (0-1)
        """
        try:
            # Convert metrics to a 0-1 scale
            crosstalk_score = max(0, min(1, (crosstalk + 60) / 60))
            reflection_score = max(0, min(1, 1 - reflections))
            impedance_score = max(0, min(1, 1 - impedance_mismatch / 100))
            
            # Weighted average
            return 0.4 * crosstalk_score + 0.3 * reflection_score + 0.3 * impedance_score
            
        except Exception as e:
            self.logger.error(f"Error calculating signal quality: {str(e)}")
            return 0.5
    
    def _calculate_radiated_emissions(self, frequency: float) -> float:
        """Calculate radiated emissions at a specific frequency.
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            float: Radiated emissions in dBμV/m
        """
        try:
            # Get all tracks
            tracks = self.board.GetTracks()
            
            # Calculate total emissions
            total_emissions = 0.0
            for track in tracks:
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                # Calculate loop area
                area = self._calculate_loop_area(track)
                
                # Calculate current (simplified)
                current = 0.1  # A
                
                # Calculate emissions using simplified model
                k = 0.01  # Emission coefficient
                emissions = k * frequency * area * current
                
                total_emissions += emissions
            
            # Convert to dBμV/m
            return 20 * math.log10(total_emissions * 1e6)
            
        except Exception as e:
            self.logger.error(f"Error calculating radiated emissions: {str(e)}")
            return 0.0
    
    def _calculate_conducted_emissions(self, frequency: float) -> float:
        """Calculate conducted emissions at a specific frequency.
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            float: Conducted emissions in dBμV
        """
        try:
            # Get all tracks
            tracks = self.board.GetTracks()
            
            # Calculate total emissions
            total_emissions = 0.0
            for track in tracks:
                if track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                # Calculate track length
                length = track.GetLength() / 1e6  # Convert nm to mm
                
                # Calculate current (simplified)
                current = 0.1  # A
                
                # Calculate emissions using simplified model
                k = 0.01  # Emission coefficient
                emissions = k * frequency * length * current
                
                total_emissions += emissions
            
            # Convert to dBμV
            return 20 * math.log10(total_emissions * 1e6)
            
        except Exception as e:
            self.logger.error(f"Error calculating conducted emissions: {str(e)}")
            return 0.0
    
    def _calculate_susceptibility(self, frequency: float) -> float:
        """Calculate susceptibility at a specific frequency.
        
        Args:
            frequency: Frequency in Hz
            
        Returns:
            float: Susceptibility in dBμV/m
        """
        try:
            # Simplified susceptibility calculation
            # In practice, you would need more sophisticated analysis
            base_susceptibility = 50.0  # dBμV/m
            frequency_factor = 20 * math.log10(frequency / 1e6)
            
            return base_susceptibility + frequency_factor
            
        except Exception as e:
            self.logger.error(f"Error calculating susceptibility: {str(e)}")
            return 50.0
    
    def _calculate_compliance_margin(self, radiated_emissions: Dict[float, float],
                                   conducted_emissions: Dict[float, float]) -> float:
        """Calculate margin to EMC standards.
        
        Args:
            radiated_emissions: Dict of frequency -> radiated emissions
            conducted_emissions: Dict of frequency -> conducted emissions
            
        Returns:
            float: Compliance margin in dB
        """
        try:
            # Calculate worst-case emissions
            max_radiated = max(radiated_emissions.values())
            max_conducted = max(conducted_emissions.values())
            
            # Calculate margins
            radiated_margin = self.config.radiated_emissions_limit - max_radiated
            conducted_margin = self.config.conducted_emissions_limit - max_conducted
            
            # Return minimum margin
            return min(radiated_margin, conducted_margin)
            
        except Exception as e:
            self.logger.error(f"Error calculating compliance margin: {str(e)}")
            return 0.0
    
    def _calculate_impedance(self, track: pcbnew.TRACK) -> float:
        """Calculate characteristic impedance of a track.
        
        Args:
            track: KiCad track object
            
        Returns:
            float: Characteristic impedance in ohms
        """
        try:
            # Get track properties
            w = track.GetWidth() / 1e6  # Convert nm to mm
            h = self.config.substrate_height
            t = self.config.copper_thickness
            er = self.config.dielectric_constant
            
            # Calculate impedance using simplified microstrip model
            z0 = 87 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))
            
            return z0
            
        except Exception as e:
            self.logger.error(f"Error calculating impedance: {str(e)}")
            return 50.0
    
    def _get_nearby_tracks(self, track: pcbnew.TRACK) -> List[pcbnew.TRACK]:
        """Get nearby tracks for crosstalk analysis.
        
        Args:
            track: Reference track
            
        Returns:
            List of nearby tracks
        """
        try:
            nearby_tracks = []
            all_tracks = self.board.GetTracks()
            
            for other_track in all_tracks:
                if other_track == track or other_track.GetType() != pcbnew.PCB_TRACE_T:
                    continue
                
                # Check if tracks are nearby
                distance = self._calculate_min_distance(track, other_track)
                if distance < 1.0:  # Within 1mm
                    nearby_tracks.append(other_track)
            
            return nearby_tracks
            
        except Exception as e:
            self.logger.error(f"Error getting nearby tracks: {str(e)}")
            return []
    
    def _calculate_loop_area(self, track: pcbnew.TRACK) -> float:
        """Calculate loop area for a track.
        
        Args:
            track: KiCad track object
            
        Returns:
            float: Loop area in mm²
        """
        try:
            # Simplified loop area calculation
            # In practice, you would need to trace the actual current path
            length = track.GetLength() / 1e6  # Convert nm to mm
            width = track.GetWidth() / 1e6  # Convert nm to mm
            
            # Assume rectangular loop
            area = length * width
            
            return area
            
        except Exception as e:
            self.logger.error(f"Error calculating loop area: {str(e)}")
            return 1.0
    
    def _calculate_min_distance(self, track1: pcbnew.TRACK, track2: pcbnew.TRACK) -> float:
        """Calculate minimum distance between tracks.
        
        Args:
            track1: First track
            track2: Second track
            
        Returns:
            float: Minimum distance in mm
        """
        try:
            # Get track endpoints
            start1 = track1.GetStart()
            end1 = track1.GetEnd()
            start2 = track2.GetStart()
            end2 = track2.GetEnd()
            
            # Calculate minimum distance between endpoints
            min_distance = float('inf')
            for p1 in [start1, end1]:
                for p2 in [start2, end2]:
                    distance = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2) / 1e6  # Convert nm to mm
                    min_distance = min(min_distance, distance)
            
            return min_distance
            
        except Exception as e:
            self.logger.error(f"Error calculating minimum distance: {str(e)}")
            return 1.0  # Default to 1mm 